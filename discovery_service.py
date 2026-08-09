"""
CompetitorDiscoveryService module for Business & Competitive Intelligence Agent.

Orchestrates full background discovery flow:
  1. Set setupStatus = PROCESSING, progress 0
  2. Generate search queries with Groq AI, progress 15
  3. Search competitor candidates via SearchService (Exa AI / Serper), progress 30
  4. Scrape candidate websites via Jina (with 7-day caching and 1s rate-limit delay), progress 55
  5. Extract candidate profiles with Groq AI, progress 70
  6. Score candidates against user's company profile with Groq AI, progress 80
  7. Rank and store top 10 competitors into DB, progress 90
  8. Generate executive summary brief with Groq AI, progress 95
  9. Mark setupStatus = COMPLETED, progress 100
"""

import asyncio
import json
import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import Any, Optional

from openai import AsyncOpenAI

from config import GROQ_API_KEY, GROQ_BASE_URL, EXTRACTION_MODEL, LLM_MODEL
from database import (
    get_company_profile_by_id,
    update_company_setup_status,
    save_discovered_competitor,
)
from scraper import scrape_website
import search_service

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)


def _clean_and_parse_json(text: str) -> Any:
    """Clean markdown backticks and parse JSON string."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


async def _call_groq_json(prompt: str, model: str = EXTRACTION_MODEL) -> Any:
    """Call Groq API with instructions to output JSON, retrying once on failure."""
    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"} if attempt == 0 else None,
                temperature=0.2,
            )
            raw = response.choices[0].message.content or ""
            return _clean_and_parse_json(raw)
        except Exception as exc:
            logger.warning("Groq JSON call attempt %d failed: %s", attempt + 1, str(exc))
            if attempt == 1:
                raise exc


def _extract_domain(url: str) -> str:
    """Extract registered domain name from URL."""
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return url.lower()


class CompetitorDiscoveryService:
    """Service handling background discovery of competitors."""

    def __init__(self, company_id: str):
        self.company_id = company_id

    async def run(self) -> None:
        """Run the full async discovery pipeline for the company."""
        logger.info("=== Starting Competitor Discovery Job for Company ID: %s ===", self.company_id)

        try:
            # Retrieve company profile from database
            company = get_company_profile_by_id(self.company_id)
            if not company:
                logger.error("Company profile not found for ID: %s", self.company_id)
                update_company_setup_status(
                    self.company_id,
                    status="FAILED",
                    progress=0,
                    current_step="Company profile not found",
                    setup_error="Company record not found in database",
                )
                return

            company_name = company.get("company_name", "")
            website = company.get("website", "")
            industry = company.get("industry", "")
            description = company.get("description", "")
            products_raw = company.get("products_or_services", [])
            products_str = (
                ", ".join(products_raw) if isinstance(products_raw, list) else str(products_raw)
            )
            customer_segments = company.get("target_customers", "")
            primary_problem = description
            business_type = company.get("company_stage") or company.get("company_size") or "B2B"
            own_domain = _extract_domain(website)

            # -----------------------------------------------------------------
            # STEP 1 — Update status to PROCESSING, progress 0
            # -----------------------------------------------------------------
            logger.info("Step 1: Starting competitive analysis...")
            update_company_setup_status(
                self.company_id,
                status="PROCESSING",
                progress=0,
                current_step="Starting competitive analysis...",
                setup_started_at=datetime.utcnow().isoformat(),
                setup_error=None,
            )

            # -----------------------------------------------------------------
            # STEP 2 — Generate search queries using Groq, progress 15
            # -----------------------------------------------------------------
            logger.info("Step 2: Generating search queries via Groq...")
            query_prompt = f"""You are a competitive intelligence analyst. Given the following company profile, generate exactly 5 search queries to find their direct competitors on the web. Focus on finding similar products, alternative tools, and competing solutions in the same space. Return only a valid JSON array of 5 strings, no explanation, no markdown, just the JSON array.

Company Name: {company_name}
Industry: {industry}
Description: {description}
Products or Services: {products_str}
Target Customers: {customer_segments}
Problem Solved: {primary_problem}
Business Type: {business_type}"""

            queries = []
            try:
                raw_queries = await _call_groq_json(query_prompt, model=EXTRACTION_MODEL)
                if isinstance(raw_queries, list):
                    queries = raw_queries
                elif isinstance(raw_queries, dict) and "queries" in raw_queries:
                    queries = raw_queries["queries"]
            except Exception as e:
                logger.warning("Failed to parse Groq query array, using default search queries: %s", e)
                queries = [
                    f"{company_name} competitors alternative",
                    f"best tools like {company_name} {industry}",
                    f"top solutions for {industry} {products_str[:30]}",
                    f"software similar to {company_name}",
                    f"{industry} competitive alternatives",
                ]

            if not queries:
                queries = [f"{company_name} competitors", f"{industry} alternatives"]

            logger.info("Generated %d search queries: %s", len(queries), queries)
            update_company_setup_status(
                self.company_id,
                status="PROCESSING",
                progress=15,
                current_step="Search queries generated...",
            )

            # -----------------------------------------------------------------
            # STEP 3 — Search for candidates, progress 30
            # -----------------------------------------------------------------
            logger.info("Step 3: Searching for candidate competitors...")
            candidate_urls: list[str] = []

            for q in queries[:5]:
                results = await search_service.search_competitors(q)
                for res in results:
                    url = res.get("url", "").strip()
                    if not url:
                        continue

                    # Filter out own company website
                    cand_domain = _extract_domain(url)
                    if own_domain and own_domain in cand_domain:
                        continue

                    # Filter blocked domains using SearchService helper
                    if not search_service._is_allowed_url(url):
                        continue

                    if url not in candidate_urls:
                        candidate_urls.append(url)

            # Keep maximum 15 candidate URLs
            candidate_urls = candidate_urls[:15]
            logger.info("Found %d candidate URLs for discovery", len(candidate_urls))

            update_company_setup_status(
                self.company_id,
                status="PROCESSING",
                progress=30,
                current_step="Searching for competitors...",
            )

            # -----------------------------------------------------------------
            # STEP 4 — Scrape each candidate with Jina, progress 55
            # -----------------------------------------------------------------
            logger.info("Step 4: Researching candidate companies via Jina...")
            scraped_candidates: list[dict] = []

            for idx, url in enumerate(candidate_urls):
                try:
                    content = await scrape_website(url)
                    if content and len(content.strip()) > 50:
                        scraped_candidates.append({"url": url, "content": content})
                    else:
                        logger.warning("Empty content scraped for candidate: %s", url)
                except Exception as exc:
                    logger.warning("Jina scrape failed for candidate %s: %s", url, str(exc))

                # Add a 1 second delay between each Jina scrape call
                if idx < len(candidate_urls) - 1:
                    await asyncio.sleep(1.0)

            logger.info("Successfully scraped %d candidates", len(scraped_candidates))
            update_company_setup_status(
                self.company_id,
                status="PROCESSING",
                progress=55,
                current_step="Researching candidate companies...",
            )

            # -----------------------------------------------------------------
            # STEP 5 — Extract competitor profile with Groq, progress 70
            # -----------------------------------------------------------------
            logger.info("Step 5: Extracting candidate profiles via Groq...")
            valid_candidates: list[dict] = []

            for item in scraped_candidates:
                url = item["url"]
                scraped_text = item["content"][:3000]

                extract_prompt = f"""You are analyzing a company website to extract structured information. Return only valid JSON, no explanation, no markdown.

Extract this structure:
{{
  "companyName": string or null,
  "website": "{url}",
  "description": string of 2 to 3 sentences maximum,
  "mainProduct": string,
  "targetCustomers": array of strings,
  "industry": string,
  "businessModel": one of B2B or B2C or Both or Unknown,
  "isActualCompany": true or false
}}

Set isActualCompany to false if this is not a real company homepage.
Set isActualCompany to false if this is a blog post, news article, comparison site, or directory listing.

Website content:
{scraped_text}"""

                try:
                    profile = await _call_groq_json(extract_prompt, model=EXTRACTION_MODEL)
                    if isinstance(profile, dict) and profile.get("isActualCompany") is True:
                        profile["website"] = url
                        if not profile.get("companyName"):
                            profile["companyName"] = _extract_domain(url).capitalize()
                        valid_candidates.append(profile)
                    else:
                        logger.info("Discarded candidate (isActualCompany=False or non-dict): %s", url)
                except Exception as exc:
                    logger.warning("Failed profile extraction for %s: %s", url, str(exc))

            logger.info("Extracted %d valid company candidates", len(valid_candidates))
            update_company_setup_status(
                self.company_id,
                status="PROCESSING",
                progress=70,
                current_step="Analyzing candidate companies...",
            )

            # -----------------------------------------------------------------
            # STEP 6 — Score each competitor with Groq, progress 80
            # -----------------------------------------------------------------
            logger.info("Step 6: Scoring competitive landscape via Groq...")
            scored_candidates: list[dict] = []

            for cand in valid_candidates:
                cand_name = cand.get("companyName") or "Unknown Candidate"
                cand_desc = cand.get("description") or ""
                cand_prod = cand.get("mainProduct") or ""
                cand_cust = cand.get("targetCustomers") or []
                cand_cust_str = ", ".join(cand_cust) if isinstance(cand_cust, list) else str(cand_cust)
                cand_ind = cand.get("industry") or ""
                cand_bm = cand.get("businessModel") or "Unknown"

                score_prompt = f"""You are a competitive intelligence analyst. Compare these two companies and score their competitive overlap. Return only valid JSON, no explanation, no markdown.

OUR COMPANY:
Name: {company_name}
Industry: {industry}
Description: {description}
Products: {products_str}
Target Customers: {customer_segments}
Problem Solved: {primary_problem}
Business Type: {business_type}

CANDIDATE COMPETITOR:
Name: {cand_name}
Description: {cand_desc}
Main Product: {cand_prod}
Target Customers: {cand_cust_str}
Industry: {cand_ind}
Business Model: {cand_bm}

Return this JSON structure:
{{
  "productSimilarity": integer 0 to 100,
  "customerOverlap": integer 0 to 100,
  "marketOverlap": integer 0 to 100,
  "businessModelOverlap": integer 0 to 100,
  "overallScore": integer 0 to 100,
  "competitorType": one of DIRECT or INDIRECT or EMERGING,
  "reason": string of 2 to 3 sentences explaining why they are a competitor,
  "confidenceScore": integer 0 to 100
}}

Scoring guide:
DIRECT means same product and same target customer, score 70 to 100.
INDIRECT means different product but solves same problem, score 40 to 70.
EMERGING means small or new company that could compete in future, score 20 to 40.
Score below 20 means not a real competitor."""

                try:
                    score_res = await _call_groq_json(score_prompt, model=EXTRACTION_MODEL)
                    if isinstance(score_res, dict):
                        overall_score = int(score_res.get("overallScore", 0))
                        if overall_score >= 20:
                            cand.update(score_res)
                            scored_candidates.append(cand)
                        else:
                            logger.info("Filtered candidate '%s' with low overallScore: %d", cand_name, overall_score)
                except Exception as exc:
                    logger.warning("Scoring failed for candidate %s: %s", cand_name, str(exc))

            logger.info("Scored %d relevant competitors (score >= 20)", len(scored_candidates))
            update_company_setup_status(
                self.company_id,
                status="PROCESSING",
                progress=80,
                current_step="Scoring competitive landscape...",
            )

            # -----------------------------------------------------------------
            # STEP 7 — Rank and store competitors, progress 90
            # -----------------------------------------------------------------
            logger.info("Step 7: Ranking and saving competitors...")
            scored_candidates.sort(key=lambda x: int(x.get("overallScore", 0)), reverse=True)
            top_competitors = scored_candidates[:10]

            for comp in top_competitors:
                save_discovered_competitor(
                    company_id=self.company_id,
                    data={
                        "name": comp.get("companyName") or "Discovered Competitor",
                        "website_url": comp.get("website"),
                        "description": comp.get("description"),
                        "type": comp.get("competitorType") or "DIRECT",
                        "source": "AI_DISCOVERED",
                        "product_similarity": int(comp.get("productSimilarity", 50)),
                        "customer_overlap": int(comp.get("customerOverlap", 50)),
                        "market_overlap": int(comp.get("marketOverlap", 50)),
                        "business_model_overlap": int(comp.get("businessModelOverlap", 50)),
                        "competitive_score": int(comp.get("overallScore", 50)),
                        "confidence_score": int(comp.get("confidenceScore", 80)),
                        "reason": comp.get("reason", "Discovered competitor in market segment."),
                    },
                )

            update_company_setup_status(
                self.company_id,
                status="PROCESSING",
                progress=90,
                current_step="Saving competitors...",
            )

            # -----------------------------------------------------------------
            # STEP 8 — Generate AI executive brief, progress 95
            # -----------------------------------------------------------------
            logger.info("Step 8: Generating executive brief via Groq...")
            top5_summary_list = []
            for c in top_competitors[:5]:
                c_name = c.get("companyName", "Competitor")
                c_type = c.get("competitorType", "DIRECT")
                c_score = c.get("overallScore", 50)
                c_reason = c.get("reason", "")
                top5_summary_list.append(f"- {c_name} ({c_type}, Score: {c_score}): {c_reason}")

            top5_str = "\n".join(top5_summary_list) if top5_summary_list else "No direct competitors detected."

            brief_prompt = f"""You are a competitive intelligence analyst. Based on the company profile and discovered competitors below, write a brief executive summary. Return only valid JSON, no explanation, no markdown.

COMPANY:
Name: {company_name}
Industry: {industry}
Description: {description}
Problem Solved: {primary_problem}

DISCOVERED COMPETITORS:
{top5_str}

Return this JSON structure:
{{
  "executiveBrief": string of 3 to 4 sentences describing the competitive landscape, main threats, and overall position,
  "mainThreats": array of up to 3 short strings each describing one threat,
  "keyOpportunity": string of 1 to 2 sentences describing one key opportunity
}}"""

            executive_brief = f"{company_name} operates in the {industry} market. Active monitoring of competitive alternatives provides strategic advantage."
            main_threats = ["Emerging competitors entering the space", "Price competition", "Feature duplication"]
            key_opportunity = f"Leverage distinct features to capture market share in {industry}."

            try:
                brief_res = await _call_groq_json(brief_prompt, model=LLM_MODEL)
                if isinstance(brief_res, dict):
                    executive_brief = brief_res.get("executiveBrief", executive_brief)
                    main_threats = brief_res.get("mainThreats", main_threats)
                    key_opportunity = brief_res.get("keyOpportunity", key_opportunity)
            except Exception as exc:
                logger.warning("Executive brief generation failed, using defaults: %s", str(exc))

            update_company_setup_status(
                self.company_id,
                status="PROCESSING",
                progress=95,
                current_step="Generating executive brief...",
                executive_brief=executive_brief,
                main_threats=main_threats,
                key_opportunity=key_opportunity,
                brief_generated_at=datetime.utcnow().isoformat(),
            )

            # -----------------------------------------------------------------
            # STEP 9 — Mark as completed, progress 100
            # -----------------------------------------------------------------
            logger.info("Step 9: Marking competitor discovery job as COMPLETED")
            update_company_setup_status(
                self.company_id,
                status="COMPLETED",
                progress=100,
                current_step="Done",
                setup_completed_at=datetime.utcnow().isoformat(),
            )
            logger.info("=== Competitor Discovery Job Completed Successfully for Company ID: %s ===", self.company_id)

        except Exception as exc:
            logger.exception("CompetitorDiscoveryJob failed with unhandled exception for company %s: %s", self.company_id, str(exc))
            update_company_setup_status(
                self.company_id,
                status="FAILED",
                progress=0,
                current_step="Setup failed",
                setup_error=str(exc),
            )


_active_discovery_tasks = set()

def run_competitor_discovery(company_id: str) -> None:
    """Helper function to execute CompetitorDiscoveryService in a background task."""
    service = CompetitorDiscoveryService(company_id)
    task = asyncio.create_task(service.run())
    _active_discovery_tasks.add(task)
    task.add_done_callback(_active_discovery_tasks.discard)


async def re_research_competitor_background(competitor_id: str, company_id: str, website: str, name: str) -> None:
    """Background job to re-research a competitor (scrape, extract, rescore)."""
    from database import (
        update_competitor_research_status,
        update_competitor_fields,
        get_company_profile_by_id,
        insert_audit_log
    )
    try:
        content = await scrape_website(website)
        company = get_company_profile_by_id(company_id) or {}
        company_name = company.get("company_name", "")
        industry = company.get("industry", "")
        description = company.get("description", "")
        products_raw = company.get("products_or_services", [])
        products_str = ", ".join(products_raw) if isinstance(products_raw, list) else str(products_raw)
        customer_segments = company.get("target_customers", "")
        primary_problem = description
        business_type = company.get("company_stage") or company.get("company_size") or "B2B"

        profile_prompt = f"""You are analyzing a company website to extract structured information. Return only valid JSON, no explanation, no markdown.

Extract this structure:
{{
  "companyName": "{name}",
  "website": "{website}",
  "description": string of 2 to 3 sentences maximum,
  "mainProduct": string,
  "targetCustomers": array of strings,
  "industry": string,
  "businessModel": one of B2B or B2C or Both or Unknown,
  "isActualCompany": true
}}

Website content:
{content[:3000]}"""

        parsed_profile = await _call_groq_json(profile_prompt)
        cand_desc = parsed_profile.get("description", f"Competitor entry for {name}.")
        cand_prod = parsed_profile.get("mainProduct") or ""
        cand_cust = parsed_profile.get("targetCustomers") or []
        cand_cust_str = ", ".join(cand_cust) if isinstance(cand_cust, list) else str(cand_cust)
        cand_ind = parsed_profile.get("industry") or ""
        cand_bm = parsed_profile.get("businessModel") or "Unknown"

        score_prompt = f"""You are a competitive intelligence analyst. Compare these two companies and score their competitive overlap. Return only valid JSON, no explanation, no markdown.

OUR COMPANY:
Name: {company_name}
Industry: {industry}
Description: {description}
Products: {products_str}
Target Customers: {customer_segments}
Problem Solved: {primary_problem}
Business Type: {business_type}

CANDIDATE COMPETITOR:
Name: {name}
Description: {cand_desc}
Main Product: {cand_prod}
Target Customers: {cand_cust_str}
Industry: {cand_ind}
Business Model: {cand_bm}

Return this JSON structure:
{{
  "productSimilarity": integer 0 to 100,
  "customerOverlap": integer 0 to 100,
  "marketOverlap": integer 0 to 100,
  "businessModelOverlap": integer 0 to 100,
  "overallScore": integer 0 to 100,
  "competitorType": one of DIRECT or INDIRECT or EMERGING,
  "reason": string of 2 to 3 sentences explaining why they are a competitor,
  "confidenceScore": integer 0 to 100
}}"""

        score_res = await _call_groq_json(score_prompt)

        update_data = {
            "description": cand_desc,
            "type": score_res.get("competitorType", "DIRECT"),
            "product_similarity": int(score_res.get("productSimilarity", 50)),
            "customer_overlap": int(score_res.get("customerOverlap", 50)),
            "market_overlap": int(score_res.get("marketOverlap", 50)),
            "business_model_overlap": int(score_res.get("businessModelOverlap", 50)),
            "competitive_score": int(score_res.get("overallScore", 50)),
            "confidence_score": int(score_res.get("confidenceScore", 80)),
            "reason": score_res.get("reason", f"Researched competitor {name}."),
        }
        
        update_competitor_fields(competitor_id, update_data)
        update_competitor_research_status(competitor_id, "IDLE")
        logger.info("Re-research complete for competitor ID: %s", competitor_id)
        
    except Exception as exc:
        logger.warning("Re-research failed for competitor %s: %s", competitor_id, str(exc))
        from database import update_competitor_research_status
        update_competitor_research_status(competitor_id, "FAILED")
