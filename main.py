"""
Main FastAPI application for Competitor Analysis AI.

Exposes two endpoints:
  - GET  /          → Health check
  - POST /analyze   → Full competitor analysis pipeline

The /analyze endpoint orchestrates: scraping → extraction → analysis →
report formatting → file save → JSON response.
"""

import logging
import re
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from models import (
    CompetitorRequest, 
    CompetitorReport, 
    CompanyProfilePayload, 
    CompanyProfileResponse, 
    CompanyProfileResponseCompany,
    AuthRequest,
    AuthResponse,
    SetupStatusResponse,
    CompetitorOut,
    CompetitorsListResponse,
    ManualCompetitorRequest,
)
from scraper import scrape_website, scrape_social
from extractor import extract_signals
from analyzer import analyze_competitor, format_report
from database import (
    save_competitor_and_report,
    get_company_profile,
    get_company_profile_by_id,
    upsert_company_profile,
    get_competitors_for_company,
    get_competitor_by_id,
    update_competitor_accepted,
    update_competitor_details,
    save_manual_competitor,
    supabase_client,
)
from auth import get_current_user
from discovery_service import run_competitor_discovery

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Competitor Analysis AI",
    version="1.0",
    description=(
        "AI-powered competitive intelligence API. Submit a competitor's name "
        "and website to receive a full business-grade analysis report."
    ),
)

# CORS — allow frontend on different port during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Startup: ensure reports directory exists
# ---------------------------------------------------------------------------
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def _slugify(text: str) -> str:
    """Convert a string to a filesystem-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
async def health_check() -> dict:
    """Health-check endpoint returning service status."""
    return {"status": "ok", "service": "competitor-analysis-ai"}


# ---------------------------------------------------------------------------
# Auth Routes
# ---------------------------------------------------------------------------

@app.post("/api/auth/signup", response_model=AuthResponse)
async def signup(req: AuthRequest) -> AuthResponse:
    """Register a new user using Supabase Auth."""
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database connection not available")
        
    try:
        response = supabase_client.auth.sign_up({
            "email": req.email,
            "password": req.password
        })
        if not response or not response.user or not response.session:
            raise HTTPException(status_code=400, detail="Signup failed or email confirmation required.")
            
        return AuthResponse(
            access_token=response.session.access_token,
            user_id=response.user.id,
            email=response.user.email
        )
    except Exception as exc:
        logger.error(f"Signup error: {str(exc)}")
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(req: AuthRequest) -> AuthResponse:
    """Login an existing user using Supabase Auth."""
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database connection not available")
        
    try:
        response = supabase_client.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password
        })
        if not response or not response.session or not response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials.")
            
        return AuthResponse(
            access_token=response.session.access_token,
            user_id=response.user.id,
            email=response.user.email
        )
    except Exception as exc:
        logger.error(f"Login error: {str(exc)}")
        raise HTTPException(status_code=401, detail="Invalid credentials.")


@app.get("/api/company/profile", response_model=CompanyProfileResponse)
async def get_company_status(user_id: str = Depends(get_current_user)) -> CompanyProfileResponse:
    """Check if the user has completed company setup and return profile."""
    company_data = get_company_profile(user_id)
    if not company_data:
        return CompanyProfileResponse(setupCompleted=False, company=None)
        
    return CompanyProfileResponse(
        setupCompleted=bool(company_data.get("setup_status") == "COMPLETED" or company_data.get("onboarding_completed")),
        company=CompanyProfileResponseCompany(
            id=str(company_data.get("id", "")),
            companyName=company_data.get("company_name", ""),
            website=company_data.get("website", ""),
            industry=company_data.get("industry", ""),
            setupStatus=company_data.get("setup_status", "PENDING"),
            executiveBrief=company_data.get("executive_brief"),
            mainThreats=company_data.get("main_threats"),
            keyOpportunity=company_data.get("key_opportunity"),
        )
    )


@app.post("/api/company/profile", response_model=CompanyProfileResponse)
async def submit_company_profile(
    payload: CompanyProfilePayload,
    user_id: str = Depends(get_current_user)
) -> CompanyProfileResponse:
    """Submit or update company profile and trigger async competitor discovery immediately."""
    data = payload.model_dump()
    data["website"] = str(data["website"])
    
    company_data = upsert_company_profile(user_id, data)
    if not company_data:
        raise HTTPException(status_code=500, detail="Failed to save company profile.")

    company_id = str(company_data.get("id", ""))
    if company_id:
        run_competitor_discovery(company_id)
        
    return CompanyProfileResponse(
        setupCompleted=True,
        company=CompanyProfileResponseCompany(
            id=company_id,
            companyName=company_data.get("company_name", ""),
            website=company_data.get("website", ""),
            industry=company_data.get("industry", ""),
            setupStatus=company_data.get("setup_status", "PROCESSING"),
            executiveBrief=company_data.get("executive_brief"),
            mainThreats=company_data.get("main_threats"),
            keyOpportunity=company_data.get("key_opportunity"),
        )
    )


# ---------------------------------------------------------------------------
# Setup Status & Discovery Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/company/setup-status", response_model=SetupStatusResponse)
async def get_setup_status(user_id: str = Depends(get_current_user)) -> SetupStatusResponse:
    """Return discovery job progress status for the user's company."""
    company = get_company_profile(user_id)
    if not company:
        return SetupStatusResponse(
            status="PENDING",
            progress=0,
            currentStep="Not started",
            completedAt=None,
            error=None
        )

    return SetupStatusResponse(
        status=company.get("setup_status", "PENDING"),
        progress=company.get("setup_progress", 0),
        currentStep=company.get("setup_current_step"),
        completedAt=company.get("setup_completed_at"),
        error=company.get("setup_error")
    )


@app.post("/api/company/trigger-discovery")
async def trigger_discovery(user_id: str = Depends(get_current_user)) -> dict:
    """Allow user/frontend to retry or trigger competitor discovery job."""
    company = get_company_profile(user_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found. Complete onboarding first.")

    company_id = str(company.get("id", ""))
    status = company.get("setup_status", "PENDING")

    if status in ("PROCESSING",):
        logger.info("Discovery job already running for company ID: %s", company_id)
        return {"status": "processing", "message": "Discovery job is already in progress."}

    run_competitor_discovery(company_id)
    return {"status": "ok", "message": "Competitor discovery triggered in background."}


# ---------------------------------------------------------------------------
# Competitors Endpoints
# ---------------------------------------------------------------------------

def _map_competitor_row(row: dict) -> CompetitorOut:
    return CompetitorOut(
        id=str(row.get("id", "")),
        name=row.get("name", ""),
        website=row.get("website_url") or row.get("website"),
        description=row.get("description"),
        type=row.get("type"),
        source=row.get("source"),
        competitiveScore=row.get("competitive_score"),
        confidenceScore=row.get("confidence_score"),
        productSimilarity=row.get("product_similarity"),
        customerOverlap=row.get("customer_overlap"),
        marketOverlap=row.get("market_overlap"),
        businessModelOverlap=row.get("business_model_overlap"),
        reason=row.get("reason"),
        isAccepted=row.get("is_accepted")
    )


@app.get("/api/competitors", response_model=CompetitorsListResponse)
async def get_competitors(user_id: str = Depends(get_current_user)) -> CompetitorsListResponse:
    """Get all discovered and manual competitors for the user's company."""
    company = get_company_profile(user_id)
    if not company:
        return CompetitorsListResponse(competitors=[], total=0, direct=0, indirect=0, emerging=0)

    company_id = str(company.get("id", ""))
    rows = get_competitors_for_company(company_id)

    competitors = [_map_competitor_row(r) for r in rows]
    total = len(competitors)
    direct = sum(1 for c in competitors if c.type == "DIRECT")
    indirect = sum(1 for c in competitors if c.type == "INDIRECT")
    emerging = sum(1 for c in competitors if c.type == "EMERGING")

    return CompetitorsListResponse(
        competitors=competitors,
        total=total,
        direct=direct,
        indirect=indirect,
        emerging=emerging
    )


@app.post("/api/competitors/{competitor_id}/accept", response_model=CompetitorOut)
async def accept_competitor(
    competitor_id: str,
    user_id: str = Depends(get_current_user)
) -> CompetitorOut:
    """Accept a competitor recommendation."""
    company = get_company_profile(user_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found.")

    company_id = str(company.get("id", ""))
    comp = get_competitor_by_id(competitor_id)

    if not comp or str(comp.get("company_id")) != company_id:
        raise HTTPException(status_code=404, detail="Competitor not found.")

    updated = update_competitor_accepted(competitor_id, True)
    if not updated:
        comp["is_accepted"] = True
        return _map_competitor_row(comp)

    return _map_competitor_row(updated)


@app.post("/api/competitors/{competitor_id}/reject", response_model=CompetitorOut)
async def reject_competitor(
    competitor_id: str,
    user_id: str = Depends(get_current_user)
) -> CompetitorOut:
    """Reject a competitor recommendation."""
    company = get_company_profile(user_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found.")

    company_id = str(company.get("id", ""))
    comp = get_competitor_by_id(competitor_id)

    if not comp or str(comp.get("company_id")) != company_id:
        raise HTTPException(status_code=404, detail="Competitor not found.")

    updated = update_competitor_accepted(competitor_id, False)
    if not updated:
        comp["is_accepted"] = False
        return _map_competitor_row(comp)

    return _map_competitor_row(updated)


async def _process_manual_competitor_background(competitor_id: str, company_id: str, website: str, name: str):
    """Scrape website with Jina and extract profile/scores with Groq in background."""
    try:
        content = await scrape_website(website)
        company = get_company_profile_by_id(company_id) or {}
        company_name = company.get("company_name", "")
        industry = company.get("industry", "")
        description = company.get("description", "")
        products_raw = company.get("products_or_services", [])
        products_str = ", ".join(products_raw) if isinstance(products_raw, list) else str(products_raw)

        import discovery_service
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

        parsed_profile = await discovery_service._call_groq_json(profile_prompt)
        cand_desc = parsed_profile.get("description", f"Manual competitor entry for {name}.")

        score_prompt = f"""You are a competitive intelligence analyst. Compare these two companies and score their competitive overlap. Return only valid JSON, no explanation, no markdown.

OUR COMPANY:
Name: {company_name}
Industry: {industry}
Description: {description}
Products: {products_str}

CANDIDATE COMPETITOR:
Name: {name}
Description: {cand_desc}
Main Product: {parsed_profile.get("mainProduct", "")}

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

        score_res = await discovery_service._call_groq_json(score_prompt)

        update_data = {
            "description": cand_desc,
            "type": score_res.get("competitorType", "DIRECT"),
            "product_similarity": int(score_res.get("productSimilarity", 50)),
            "customer_overlap": int(score_res.get("customerOverlap", 50)),
            "market_overlap": int(score_res.get("marketOverlap", 50)),
            "business_model_overlap": int(score_res.get("businessModelOverlap", 50)),
            "competitive_score": int(score_res.get("overallScore", 50)),
            "confidence_score": int(score_res.get("confidenceScore", 80)),
            "reason": score_res.get("reason", f"Manually added competitor {name}."),
        }
        update_competitor_details(competitor_id, update_data)
        logger.info("Background processing complete for manual competitor ID: %s", competitor_id)
    except Exception as exc:
        logger.warning("Background processing failed for manual competitor %s: %s", competitor_id, str(exc))


@app.post("/api/competitors/manual", response_model=CompetitorOut)
async def add_manual_competitor(
    req: ManualCompetitorRequest,
    user_id: str = Depends(get_current_user)
) -> CompetitorOut:
    """Manually add a competitor, returning immediately and extracting details in background."""
    company = get_company_profile(user_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found.")

    company_id = str(company.get("id", ""))
    row = save_manual_competitor(company_id, req.name, req.website)

    if not row:
        row = {
            "id": f"manual-{int(datetime.utcnow().timestamp())}",
            "name": req.name,
            "website_url": req.website,
            "source": "MANUAL",
            "is_accepted": True
        }

    competitor_id = str(row.get("id", ""))
    if competitor_id:
        asyncio.create_task(_process_manual_competitor_background(competitor_id, company_id, req.website, req.name))

    return _map_competitor_row(row)


@app.post("/analyze", response_model=CompetitorReport)
async def analyze(req: CompetitorRequest) -> CompetitorReport:
    """Run the full competitor analysis pipeline.

    Steps:
        1. Scrape the competitor's website using Crawl4AI.
        2. Best-effort scrape any provided social URLs.
        3. Extract structured signals from scraped content via LLM.
        4. Perform deep competitive analysis via LLM.
        5. Format analysis as a polished Markdown report.
        6. Save the report to disk.
        7. Return a CompetitorReport JSON response.

    Args:
        req: A CompetitorRequest with company_name, website_url, etc.

    Returns:
        CompetitorReport containing structured analysis + full Markdown report.

    Raises:
        HTTPException: 500 if any step in the pipeline fails.
    """
    try:
        # --- 1. Scrape website ------------------------------------------------
        logger.info("=== Pipeline start: %s (%s) ===", req.company_name, req.website_url)
        website_content = await scrape_website(str(req.website_url))

        # --- 2. Scrape social URLs (best-effort) -----------------------------
        social_parts: list[str] = []
        for platform, social_url in req.social_urls.items():
            logger.info("Scraping social: %s → %s", platform, social_url)
            social_content = await scrape_social(social_url)
            if social_content:
                social_parts.append(f"\n\n[{platform.upper()}]\n{social_content}")

        # --- 3. Combine all content ------------------------------------------
        full_content = website_content + "".join(social_parts)
        logger.info("Total scraped content: %d characters", len(full_content))

        # --- 4. Extract signals -----------------------------------------------
        extracted = await extract_signals(full_content, req.company_name)
        logger.info("Extraction complete — keys: %s", list(extracted.keys()))

        # --- 5. Analyze -------------------------------------------------------
        request_data = req.model_dump()
        # Convert HttpUrl to plain string for serialisation
        request_data["website_url"] = str(request_data["website_url"])
        analysis = await analyze_competitor(extracted, request_data)
        logger.info("Analysis complete for %s", req.company_name)

        # --- 6. Format Markdown report ----------------------------------------
        markdown_report = await format_report(analysis, req.company_name)

        # --- 7. Save report to disk -------------------------------------------
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        slug = _slugify(req.company_name)
        report_filename = f"{slug}_{timestamp}.md"
        report_path = REPORTS_DIR / report_filename
        report_path.write_text(markdown_report, encoding="utf-8")
        logger.info("Report saved to disk: %s", report_path)

        # --- 8. Save report & competitor to Supabase --------------------------
        db_saved = await save_competitor_and_report(
            req_data=request_data,
            extracted=extracted,
            analysis=analysis,
            markdown_report=markdown_report,
        )
        if db_saved:
            logger.info("Saved to Supabase: competitor_id=%s, report_id=%s", db_saved.get("competitor_id"), db_saved.get("report_id"))

        # --- 9. Build response ------------------------------------------------
        report = CompetitorReport(
            company_name=req.company_name,
            executive_summary=analysis.get("executive_summary", ""),
            snapshot=analysis.get("competitor_snapshot", {}),
            strengths=analysis.get("strengths", []),
            weaknesses=analysis.get("weaknesses", []),
            opportunities=analysis.get("opportunities_for_us", []),
            threats=analysis.get("threats_to_us", []),
            swot=analysis.get("swot", {}),
            next_steps=analysis.get("next_steps", []),
            differentiation_strategy=analysis.get("differentiation_strategy", ""),
            full_markdown_report=markdown_report,
            generated_at=datetime.utcnow(),
        )

        logger.info("=== Pipeline complete: %s ===", req.company_name)
        return report

    except Exception as exc:
        logger.exception("Pipeline failed for %s: %s", req.company_name, str(exc))
        raise HTTPException(
            status_code=500,
            detail=f"Analysis pipeline failed: {str(exc)}",
        ) from exc


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
