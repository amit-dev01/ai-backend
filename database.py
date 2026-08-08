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


def get_company_profile_by_id(company_id: str) -> Optional[Dict[str, Any]]:
    """Fetch the company profile by company UUID."""
    if not supabase_client:
        return None

    try:
        response = (
            supabase_client.table("companies")
            .select("*")
            .eq("id", company_id)
            .limit(1)
            .execute()
        )
        if response and response.data:
            return response.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to fetch company profile by id %s: %s", company_id, str(exc))
        return None


def save_manual_competitor(company_id: str, name: str, website_url: str) -> Optional[Dict[str, Any]]:
    """Save a manually added competitor with source=MANUAL and is_accepted=True."""
    if not supabase_client:
        return None

    payload = {
        "company_id": company_id,
        "name": name,
        "website_url": website_url,
        "source": "MANUAL",
        "is_accepted": True,
    }

    try:
        result = supabase_client.table("competitors").insert(payload).execute()
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to save manual competitor '%s': %s", name, str(exc))
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


# ---------------------------------------------------------------------------
# Discovery pipeline helpers — added for competitor discovery feature
# ---------------------------------------------------------------------------

def update_company_setup_status(
    company_id: str,
    status: str,
    progress: int,
    current_step: str,
    **kwargs: Any,
) -> bool:
    """Update setup status fields on the companies table.

    Args:
        company_id: The UUID of the company row to update.
        status: One of PENDING, PROCESSING, COMPLETED, FAILED.
        progress: Integer 0–100.
        current_step: Human-readable step description.
        **kwargs: Optional additional fields (setup_started_at, setup_completed_at,
                  setup_error, executive_brief, main_threats, key_opportunity,
                  brief_generated_at).

    Returns:
        True if update succeeded, False otherwise.
    """
    if not supabase_client:
        return False

    payload: Dict[str, Any] = {
        "setup_status": status,
        "setup_progress": progress,
        "setup_current_step": current_step,
    }
    payload.update(kwargs)

    try:
        supabase_client.table("companies").update(payload).eq("id", company_id).execute()
        return True
    except Exception as exc:
        logger.exception("Failed to update company setup status for %s: %s", company_id, str(exc))
        return False


def save_discovered_competitor(company_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Insert a newly discovered competitor into the competitors table.

    Args:
        company_id: The UUID of the owning company.
        data: Dict with keys: name, website_url, description, type, source,
              product_similarity, customer_overlap, market_overlap,
              business_model_overlap, competitive_score, confidence_score,
              reason. is_accepted is always set to None (pending review).

    Returns:
        The inserted row dict, or None on failure.
    """
    if not supabase_client:
        return None

    payload: Dict[str, Any] = {
        "company_id": company_id,
        "name": data.get("name"),
        "website_url": data.get("website_url"),
        "description": data.get("description"),
        "type": data.get("type"),
        "source": data.get("source", "AI_DISCOVERED"),
        "product_similarity": data.get("product_similarity"),
        "customer_overlap": data.get("customer_overlap"),
        "market_overlap": data.get("market_overlap"),
        "business_model_overlap": data.get("business_model_overlap"),
        "competitive_score": data.get("competitive_score"),
        "confidence_score": data.get("confidence_score"),
        "reason": data.get("reason"),
        "is_accepted": None,  # pending review
    }

    try:
        result = supabase_client.table("competitors").insert(payload).execute()
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to save discovered competitor '%s': %s", data.get("name"), str(exc))
        return None


def get_competitors_for_company(company_id: str) -> list[Dict[str, Any]]:
    """Return all competitors for a given company.

    Args:
        company_id: The UUID of the company.

    Returns:
        List of competitor dicts (may be empty).
    """
    if not supabase_client:
        return []

    try:
        result = (
            supabase_client.table("competitors")
            .select("*")
            .eq("company_id", company_id)
            .order("competitive_score", desc=True)
            .execute()
        )
        return result.data if result and result.data else []
    except Exception as exc:
        logger.exception("Failed to get competitors for company %s: %s", company_id, str(exc))
        return []


def get_competitor_by_id(competitor_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single competitor row by its UUID.

    Args:
        competitor_id: UUID of the competitor.

    Returns:
        Competitor dict or None.
    """
    if not supabase_client:
        return None

    try:
        result = (
            supabase_client.table("competitors")
            .select("*")
            .eq("id", competitor_id)
            .limit(1)
            .execute()
        )
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to get competitor %s: %s", competitor_id, str(exc))
        return None


def update_competitor_accepted(competitor_id: str, is_accepted: bool) -> Optional[Dict[str, Any]]:
    """Set is_accepted to True or False on a competitor.

    Args:
        competitor_id: UUID of the competitor to update.
        is_accepted: True = accepted, False = rejected.

    Returns:
        Updated competitor dict or None on failure.
    """
    if not supabase_client:
        return None

    try:
        result = (
            supabase_client.table("competitors")
            .update({"is_accepted": is_accepted})
            .eq("id", competitor_id)
            .execute()
        )
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to update competitor acceptance %s: %s", competitor_id, str(exc))
        return None


def update_competitor_details(competitor_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update description and score fields on an existing competitor row.

    Used after background scraping of a manually added competitor.

    Args:
        competitor_id: UUID of the competitor to update.
        data: Dict of fields to update (description, type, product_similarity, etc.).

    Returns:
        Updated competitor dict or None on failure.
    """
    if not supabase_client:
        return None

    allowed_fields = {
        "description", "type", "product_similarity", "customer_overlap",
        "market_overlap", "business_model_overlap", "competitive_score",
        "confidence_score", "reason",
    }
    payload = {k: v for k, v in data.items() if k in allowed_fields}

    if not payload:
        return None

    try:
        result = (
            supabase_client.table("competitors")
            .update(payload)
            .eq("id", competitor_id)
            .execute()
        )
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to update competitor details %s: %s", competitor_id, str(exc))
        return None

