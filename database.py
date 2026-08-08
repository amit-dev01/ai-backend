"""
Supabase database module for Competitor Analysis AI.

Manages storing competitors and analysis reports into Supabase tables:
  - public.competitors (id, name, website_url, created_at)
  - public.reports (id, competitor_id, tracking_data, intelligence_data, strategy_data, recommendation_data, prediction_data, created_at)
"""

import logging
from typing import Optional, Dict, Any
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

supabase_client: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully (%s)", SUPABASE_URL)
    except Exception as e:
        logger.warning("Failed to initialize Supabase client: %s", str(e))


async def save_competitor_and_report(
    req_data: Dict[str, Any],
    extracted: Dict[str, Any],
    analysis: Dict[str, Any],
    markdown_report: str,
) -> Optional[Dict[str, Any]]:
    """Save analysis results to Supabase competitors and reports tables.

    Args:
        req_data: Original request payload as dict.
        extracted: Signals extracted from scraped content.
        analysis: Structured intelligence analysis dict.
        markdown_report: Polished Markdown report string.

    Returns:
        Dict with saved competitor_id and report_id, or None if save failed.
    """
    if not supabase_client:
        logger.warning("Supabase client is not available. Skipping DB save.")
        return None

    try:
        company_name = req_data.get("company_name", "").strip()
        website_url = str(req_data.get("website_url", "")).strip()

        # 1. Check or insert competitor in 'competitors' table
        competitor_id = None

        if website_url:
            existing = (
                supabase_client.table("competitors")
                .select("id")
                .eq("website_url", website_url)
                .execute()
            )
            if existing and existing.data:
                competitor_id = existing.data[0]["id"]

        if not competitor_id and company_name:
            existing = (
                supabase_client.table("competitors")
                .select("id")
                .eq("name", company_name)
                .execute()
            )
            if existing and existing.data:
                competitor_id = existing.data[0]["id"]

        # Insert new competitor if not found
        if not competitor_id:
            new_comp = (
                supabase_client.table("competitors")
                .insert({"name": company_name, "website_url": website_url})
                .execute()
            )
            if new_comp and new_comp.data:
                competitor_id = new_comp.data[0]["id"]
                logger.info("Inserted new competitor '%s' with id: %s", company_name, competitor_id)

        # 2. Insert report in 'reports' table
        tracking_data = {
            "industry": req_data.get("industry"),
            "our_company_context": req_data.get("our_company_context"),
            "focus_areas": req_data.get("focus_areas", []),
            "social_urls": req_data.get("social_urls", {}),
            "website_url": website_url,
        }

        intelligence_data = {
            "executive_summary": analysis.get("executive_summary", ""),
            "competitor_snapshot": analysis.get("competitor_snapshot", {}),
            "strengths": analysis.get("strengths", []),
            "weaknesses": analysis.get("weaknesses", []),
            "extracted_signals": extracted,
        }

        strategy_data = {
            "swot": analysis.get("swot", {}),
            "differentiation_strategy": analysis.get("differentiation_strategy", ""),
            "opportunities_for_us": analysis.get("opportunities_for_us", []),
            "threats_to_us": analysis.get("threats_to_us", []),
        }

        recommendation_data = {
            "next_steps": analysis.get("next_steps", [])
        }

        prediction_data = {
            "full_markdown_report": markdown_report
        }

        report_payload: Dict[str, Any] = {
            "tracking_data": tracking_data,
            "intelligence_data": intelligence_data,
            "strategy_data": strategy_data,
            "recommendation_data": recommendation_data,
            "prediction_data": prediction_data,
        }

        if competitor_id:
            report_payload["competitor_id"] = competitor_id

        new_report = (
            supabase_client.table("reports")
            .insert(report_payload)
            .execute()
        )

        if new_report and new_report.data:
            report_id = new_report.data[0]["id"]
            logger.info("Inserted report into Supabase with id: %s", report_id)
            return {"competitor_id": competitor_id, "report_id": report_id}
        else:
            logger.warning("Inserted report failed or returned empty response.")
            return None

    except Exception as exc:
        logger.exception("Failed to save data to Supabase: %s", str(exc))
        return None

def get_company_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch the company profile for the authenticated user."""
    if not supabase_client:
        return None
        
    try:
        response = (
            supabase_client.table("companies")
            .select("*")
            .eq("owner_id", user_id)
            .limit(1)
            .execute()
        )
        if response and response.data:
            return response.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to fetch company profile: %s", str(exc))
        return None

def upsert_company_profile(user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Insert or update the company profile for a user."""
    if not supabase_client:
        return None
        
    payload = {
        "owner_id": user_id,
        "company_name": data.get("companyName"),
        "website": str(data.get("website")),
        "industry": data.get("industry"),
        "description": data.get("description"),
        "products_or_services": data.get("productsOrServices", []),
        "target_customers": data.get("targetCustomers"),
        "company_stage": data.get("companyStage"),
        "company_size": data.get("companySize"),
        "excluded_competitors": data.get("excludedCompetitors", []),
        "onboarding_completed": True
    }
    
    try:
        existing = get_company_profile(user_id)
        
        if existing:
            response = (
                supabase_client.table("companies")
                .update(payload)
                .eq("owner_id", user_id)
                .execute()
            )
        else:
            response = (
                supabase_client.table("companies")
                .insert(payload)
                .execute()
            )
            
        if response and response.data:
            company_data = response.data[0]
            company_id = company_data.get("id")
            
            # Save competitors if provided
            competitors = data.get("competitors", [])
            if competitors and company_id:
                for comp in competitors:
                    comp_payload = {
                        "company_id": company_id,
                        "name": comp.get("name"),
                        "website_url": comp.get("website"),
                        "source": "MANUAL"
                    }
                    supabase_client.table("competitors").insert(comp_payload).execute()

            return company_data
        return None
    except Exception as exc:
        logger.exception("Failed to upsert company profile: %s", str(exc))
        return None
