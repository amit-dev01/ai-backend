"""
Supabase database module for Competitor Analysis AI.

Manages storing competitors and analysis reports into Supabase tables:
  - public.competitors (id, name, website_url, created_at)
  - public.reports (id, competitor_id, tracking_data, intelligence_data, strategy_data, recommendation_data, prediction_data, created_at)
"""

import logging
from datetime import datetime, timedelta
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
        logger.warning("Failed to fetch company profile by id %s: %s", company_id, str(exc))
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


def update_company_profile_partial(company_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update only provided fields of the company profile."""
    if not supabase_client or not payload:
        return None
    try:
        result = supabase_client.table("companies").update(payload).eq("id", company_id).execute()
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to update company profile for %s: %s", company_id, str(exc))
        return None


def update_company_settings(company_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update company monitoring and settings fields."""
    if not supabase_client or not payload:
        return None
    try:
        result = supabase_client.table("companies").update(payload).eq("id", company_id).execute()
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to update company settings for %s: %s", company_id, str(exc))
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
    """Insert or update a discovered competitor using deduplication logic."""
    if not supabase_client:
        return None

    website_url = data.get("website_url")
    name = data.get("name")
    
    # 1. Check for deduplication by website domain or normalized name
    existing_comp = None
    if website_url:
        # Simple domain extraction for check
        domain = website_url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0].lower()
        res = supabase_client.table("competitors").select("*").eq("company_id", company_id).ilike("website_url", f"%{domain}%").execute()
        if res and res.data:
            existing_comp = res.data[0]
            
    if not existing_comp and name:
        res = supabase_client.table("competitors").select("*").eq("company_id", company_id).ilike("name", name).execute()
        if res and res.data:
            existing_comp = res.data[0]

    payload: Dict[str, Any] = {
        "description": data.get("description"),
        "product_similarity": data.get("product_similarity"),
        "customer_overlap": data.get("customer_overlap"),
        "market_overlap": data.get("market_overlap"),
        "business_model_overlap": data.get("business_model_overlap"),
        "competitive_score": data.get("competitive_score"),
        "confidence_score": data.get("confidence_score"),
        "reason": data.get("reason"),
    }

    try:
        if existing_comp:
            # Update only if new score is higher
            old_score = existing_comp.get("competitive_score") or 0
            new_score = data.get("competitive_score") or 0
            if new_score > old_score:
                result = supabase_client.table("competitors").update(payload).eq("id", existing_comp["id"]).execute()
                if result and result.data:
                    return result.data[0]
            return existing_comp
        else:
            # Insert new
            payload.update({
                "company_id": company_id,
                "name": name,
                "website_url": website_url,
                "type": data.get("type"),
                "source": data.get("source", "AI_DISCOVERED"),
                "is_accepted": None,
            })
            result = supabase_client.table("competitors").insert(payload).execute()
            if result and result.data:
                return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to save discovered competitor '%s': %s", name, str(exc))
        return None


def get_competitors_for_company(
    company_id: str,
    status: str = "active",
    comp_type: Optional[str] = None,
    source: Optional[str] = None,
    accepted: Optional[str] = None
) -> list[Dict[str, Any]]:
    """Return all competitors for a given company with filters."""
    if not supabase_client:
        return []

    try:
        query = supabase_client.table("competitors").select("*").eq("company_id", company_id)

        if status == "active":
            query = query.eq("is_active", True)
        elif status == "archived":
            query = query.eq("is_active", False)

        if comp_type:
            # Match against both 'type' and 'custom_type' columns because effectiveType = custom_type || type
            query = query.or_(f"type.eq.{comp_type},custom_type.eq.{comp_type}")

        if source:
            query = query.eq("source", source)

        if accepted == "true":
            query = query.eq("is_accepted", True)
        elif accepted == "false":
            query = query.eq("is_accepted", False)
        elif accepted == "pending":
            query = query.is_("is_accepted", "null")

        result = query.order("competitive_score", desc=True).execute()
        return result.data if result and result.data else []
    except Exception as exc:
        logger.warning("Failed to get competitors for company %s: %s", company_id, str(exc))
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
        logger.warning("Failed to get competitor %s: %s", competitor_id, str(exc))
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


def update_competitor_fields(competitor_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update any allowed field on a competitor."""
    if not supabase_client or not payload:
        return None
    try:
        result = supabase_client.table("competitors").update(payload).eq("id", competitor_id).execute()
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to update competitor fields %s: %s", competitor_id, str(exc))
        return None


def update_competitor_research_status(competitor_id: str, status: str) -> None:
    """Update the research_status and optionally last_researched_at."""
    if not supabase_client:
        return
    payload = {"research_status": status}
    if status == "IDLE":
        payload["last_researched_at"] = datetime.utcnow().isoformat()
    try:
        supabase_client.table("competitors").update(payload).eq("id", competitor_id).execute()
    except Exception as exc:
        logger.exception("Failed to update research status for %s: %s", competitor_id, str(exc))


def delete_competitor_permanently(competitor_id: str) -> bool:
    """Delete a competitor permanently."""
    if not supabase_client:
        return False
    try:
        supabase_client.table("competitors").delete().eq("id", competitor_id).execute()
        return True
    except Exception as exc:
        logger.exception("Failed to delete competitor %s: %s", competitor_id, str(exc))
        return False


def insert_audit_log(company_id: str, user_id: str, action: str, entity_type: str, entity_id: str, metadata: dict) -> None:
    """Insert an audit log entry. Fails silently."""
    if not supabase_client:
        return
    payload = {
        "company_id": company_id,
        "user_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "metadata": metadata,
    }
    try:
        supabase_client.table("audit_logs").insert(payload).execute()
    except Exception as exc:
        logger.warning("Failed to insert audit log for action %s: %s", action, str(exc))


def get_audit_logs(company_id: str, limit: int = 20, offset: int = 0) -> tuple[list[Dict[str, Any]], int]:
    """Fetch audit logs for a company."""
    if not supabase_client:
        return [], 0
    try:
        result = (
            supabase_client.table("audit_logs")
            .select("*", count="exact")
            .eq("company_id", company_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        logs = result.data if result and result.data else []
        total = result.count if result and result.count is not None else len(logs)
        return logs, total
    except Exception as exc:
        logger.exception("Failed to get audit logs for %s: %s", company_id, str(exc))
        return [], 0


# ---------------------------------------------------------------------------
# Phase 2 — Live Competitor Monitoring Helpers
# ---------------------------------------------------------------------------

def get_accepted_competitors_for_company(company_id: str) -> list[Dict[str, Any]]:
    """Fetch accepted competitors for a company."""
    if not supabase_client:
        return []
    try:
        result = (
            supabase_client.table("competitors")
            .select("*")
            .eq("company_id", company_id)
            .eq("is_accepted", True)
            .execute()
        )
        return result.data if result and result.data else []
    except Exception as exc:
        logger.exception("Failed to get accepted competitors for %s: %s", company_id, str(exc))
        return []


def get_document_by_url(url: str, within_hours: int = 24) -> Optional[Dict[str, Any]]:
    """Check if a document with this source_url exists within the last N hours."""
    if not supabase_client:
        return None
    try:
        result = (
            supabase_client.table("documents")
            .select("*")
            .eq("source_url", url)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if result and result.data:
            doc = result.data[0]
            created_at_str = doc.get("created_at")
            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                now = datetime.now(created_at.tzinfo)
                if (now - created_at).total_seconds() < (within_hours * 3600):
                    return doc
        return None
    except Exception as exc:
        logger.exception("Failed to check duplicate document URL %s: %s", url, str(exc))
        return None


def _coalesce(*keys_and_data) -> Any:
    """Return the first non-None value from a dict using a list of key aliases.

    Unlike `or` chaining, this preserves falsy values like 0 and empty string.
    Usage: _coalesce(data, "camelKey", "snake_key")
    """
    data = keys_and_data[0]
    for key in keys_and_data[1:]:
        val = data.get(key)
        if val is not None:
            return val
    return None


def save_document(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Save a processed document to the documents table."""
    if not supabase_client:
        return None
    now_str = datetime.utcnow().isoformat()
    # Use _coalesce instead of `or` so that zero/falsy numeric values are preserved
    payload = {
        "competitor_id": _coalesce(data, "competitor_id", "competitorId"),
        "company_id": _coalesce(data, "company_id", "companyId"),
        "source_url": _coalesce(data, "source_url", "sourceUrl"),
        "title": data.get("title"),
        "published_date": _coalesce(data, "published_date", "publishedDate"),
        "raw_content": _coalesce(data, "raw_content", "rawContent"),
        "summary": data.get("summary"),
        "event_type": _coalesce(data, "event_type", "eventType"),
        "sentiment": data.get("sentiment"),
        # Numeric fields: use _coalesce so 0 is stored correctly, not replaced by None
        "sentiment_confidence": _coalesce(data, "sentiment_confidence", "sentimentConfidence"),
        "relevance_score": _coalesce(data, "relevance_score", "relevanceScore"),
        "relevance_reason": _coalesce(data, "relevance_reason", "relevanceReason"),
        "impact_score": _coalesce(data, "impact_score", "impactScore"),
        "impact_label": _coalesce(data, "impact_label", "impactLabel"),
        "is_processed": data.get("is_processed", data.get("isProcessed", True)),
        "created_at": now_str,
        "updated_at": now_str,
    }
    try:
        result = supabase_client.table("documents").insert(payload).execute()
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to save document: %s", str(exc))
        return None


def get_url_cache(url: str) -> Optional[Dict[str, Any]]:
    """Get cached URL scraping record."""
    if not supabase_client:
        return None
    try:
        result = (
            supabase_client.table("url_cache")
            .select("*")
            .eq("url", url)
            .limit(1)
            .execute()
        )
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to fetch URL cache for %s: %s", url, str(exc))
        return None


def upsert_url_cache(url: str, content_hash: str) -> Optional[Dict[str, Any]]:
    """Insert or update URL cache record."""
    if not supabase_client:
        return None
    now_str = datetime.utcnow().isoformat()
    payload = {
        "url": url,
        "scraped_at": now_str,
        "content_hash": content_hash,
    }
    try:
        existing = get_url_cache(url)
        if existing:
            result = (
                supabase_client.table("url_cache")
                .update(payload)
                .eq("url", url)
                .execute()
            )
        else:
            result = (
                supabase_client.table("url_cache")
                .insert(payload)
                .execute()
            )
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to upsert URL cache for %s: %s", url, str(exc))
        return None


def create_monitoring_job(company_id: str, competitor_id: Optional[str], job_type: str) -> Optional[Dict[str, Any]]:
    """Create a monitoring job record with status RUNNING."""
    if not supabase_client:
        return None
    now_str = datetime.utcnow().isoformat()
    payload = {
        "company_id": company_id,
        "competitor_id": competitor_id,
        "job_type": job_type,
        "status": "RUNNING",
        "progress": 0,
        "current_step": "Starting check...",
        "documents_found": 0,
        "documents_processed": 0,
        "started_at": now_str,
    }
    try:
        result = supabase_client.table("monitoring_jobs").insert(payload).execute()
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to create monitoring job: %s", str(exc))
        return None


def update_monitoring_job(
    job_id: str,
    status: str,
    documents_found: int,
    documents_processed: int,
    progress: int = 0,
    current_step: str = "",
    error: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Update monitoring job status and counters."""
    if not supabase_client:
        return None
    now_str = datetime.utcnow().isoformat()
    payload = {
        "status": status,
        "documents_found": documents_found,
        "documents_processed": documents_processed,
        "progress": progress,
        "current_step": current_step,
        "error": error,
    }
    if status in ("COMPLETED", "FAILED"):
        payload["completed_at"] = now_str
    try:
        result = (
            supabase_client.table("monitoring_jobs")
            .update(payload)
            .eq("id", job_id)
            .execute()
        )
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to update monitoring job %s: %s", job_id, str(exc))
        return None


def cleanup_stale_monitoring_jobs(company_id: str, stale_after_minutes: int = 30) -> int:
    """Mark RUNNING monitoring jobs older than stale_after_minutes as FAILED.

    This prevents stuck jobs (from crashes or server restarts) from permanently
    blocking future /check-now requests via the 409 active-job guard.

    Returns:
        Number of stale jobs cleaned up.
    """
    if not supabase_client:
        return 0
    try:
        cutoff = (datetime.utcnow() - timedelta(minutes=stale_after_minutes)).isoformat()
        # Find stale RUNNING jobs for this company
        stale = (
            supabase_client.table("monitoring_jobs")
            .select("id")
            .eq("company_id", company_id)
            .eq("status", "RUNNING")
            .lt("started_at", cutoff)
            .execute()
        )
        if not stale or not stale.data:
            return 0
        stale_ids = [r["id"] for r in stale.data]
        now_str = datetime.utcnow().isoformat()
        for job_id in stale_ids:
            supabase_client.table("monitoring_jobs").update({
                "status": "FAILED",
                "error": f"Job timed out after {stale_after_minutes} minutes (server restart or crash).",
                "completed_at": now_str,
            }).eq("id", job_id).execute()
        logger.warning("Cleaned up %d stale monitoring job(s) for company %s", len(stale_ids), company_id)
        return len(stale_ids)
    except Exception as exc:
        logger.exception("Failed to cleanup stale monitoring jobs for %s: %s", company_id, str(exc))
        return 0


def get_active_monitoring_job(company_id: str) -> Optional[Dict[str, Any]]:
    """Check if a monitoring job is currently running for the company."""
    if not supabase_client:
        return None
    try:
        result = (
            supabase_client.table("monitoring_jobs")
            .select("*")
            .eq("company_id", company_id)
            .eq("status", "RUNNING")
            .limit(1)
            .execute()
        )
        if result and result.data:
            return result.data[0]
        return None
    except Exception as exc:
        logger.exception("Failed to check active monitoring job for %s: %s", company_id, str(exc))
        return None


def get_monitoring_jobs_history(company_id: str, limit: int = 20) -> list[Dict[str, Any]]:
    """Fetch monitoring jobs history for a company."""
    if not supabase_client:
        return []
    try:
        result = (
            supabase_client.table("monitoring_jobs")
            .select("*")
            .eq("company_id", company_id)
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data if result and result.data else []
    except Exception as exc:
        logger.exception("Failed to get monitoring jobs history for %s: %s", company_id, str(exc))
        return []


def get_intelligence_feed(
    company_id: str,
    competitor_id: Optional[str] = None,
    event_type: Optional[str] = None,
    impact_label: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> tuple[list[Dict[str, Any]], int]:
    """Query intelligence feed documents for a company."""
    if not supabase_client:
        return [], 0
    try:
        query = (
            supabase_client.table("documents")
            .select("*, competitors(name)", count="exact")
            .eq("company_id", company_id)
            .eq("is_processed", True)
        )
        if competitor_id:
            query = query.eq("competitor_id", competitor_id)
        if event_type:
            query = query.eq("event_type", event_type)
        if impact_label:
            query = query.eq("impact_label", impact_label)

        result = (
            query.order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        docs = result.data if result and result.data else []
        total = result.count if result and result.count is not None else len(docs)
        
        # Flatten competitor name
        for d in docs:
            comp_obj = d.get("competitors")
            if isinstance(comp_obj, dict):
                d["competitor_name"] = comp_obj.get("name")
            elif isinstance(comp_obj, list) and comp_obj:
                d["competitor_name"] = comp_obj[0].get("name")
        return docs, total
    except Exception as exc:
        logger.exception("Failed to get intelligence feed for %s: %s", company_id, str(exc))
        return [], 0


def get_recent_intelligence_documents(company_id: str, days: int = 7, limit: int = 20) -> list[Dict[str, Any]]:
    """Fetch top documents from recent days ordered by impact_score desc."""
    if not supabase_client:
        return []
    try:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        result = (
            supabase_client.table("documents")
            .select("*, competitors(name)")
            .eq("company_id", company_id)
            .eq("is_processed", True)
            .gte("created_at", cutoff)
            .order("impact_score", desc=True)
            .limit(limit)
            .execute()
        )
        docs = result.data if result and result.data else []
        for d in docs:
            comp_obj = d.get("competitors")
            if isinstance(comp_obj, dict):
                d["competitor_name"] = comp_obj.get("name")
            elif isinstance(comp_obj, list) and comp_obj:
                d["competitor_name"] = comp_obj[0].get("name")
        return docs
    except Exception as exc:
        logger.exception("Failed to get recent intelligence documents for %s: %s", company_id, str(exc))
        return []


def get_intelligence_stats(company_id: str) -> Dict[str, Any]:
    """Calculate aggregated stats for intelligence collected."""
    if not supabase_client:
        return {
            "totalDocuments": 0,
            "documentsThisWeek": 0,
            "criticalEvents": 0,
            "highEvents": 0,
            "mediumEvents": 0,
            "lowEvents": 0,
            "byCompetitor": [],
            "byEventType": []
        }
    try:
        # Capped at 500 rows to prevent performance degradation as documents accumulate.
        # Stats are sampled from the most recent 500 processed documents.
        res = (
            supabase_client.table("documents")
            .select("*, competitors(id, name)")
            .eq("company_id", company_id)
            .eq("is_processed", True)
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )
        docs = res.data if res and res.data else []
        total_docs = len(docs)

        now = datetime.utcnow()
        cutoff_7d = now - timedelta(days=7)
        docs_this_week = 0
        critical = 0
        high = 0
        medium = 0
        low = 0

        comp_map: Dict[str, Dict[str, Any]] = {}
        event_map: Dict[str, int] = {}

        for d in docs:
            created_str = d.get("created_at")
            if created_str:
                dt = datetime.fromisoformat(created_str.replace("Z", "+00:00")).replace(tzinfo=None)
                if dt >= cutoff_7d:
                    docs_this_week += 1

            label = d.get("impact_label")
            if label == "CRITICAL":
                critical += 1
            elif label == "HIGH":
                high += 1
            elif label == "MEDIUM":
                medium += 1
            elif label == "LOW":
                low += 1

            etype = d.get("event_type", "OTHER")
            event_map[etype] = event_map.get(etype, 0) + 1

            comp_id = d.get("competitor_id")
            comp_obj = d.get("competitors")
            comp_name = "Unknown Competitor"
            if isinstance(comp_obj, dict):
                comp_name = comp_obj.get("name", comp_name)

            if comp_id:
                if comp_id not in comp_map:
                    comp_map[comp_id] = {
                        "competitorId": comp_id,
                        "competitorName": comp_name,
                        "documentCount": 0,
                        "latestEvent": etype,
                        "latestEventDate": created_str,
                    }
                comp_map[comp_id]["documentCount"] += 1
                if created_str and (comp_map[comp_id]["latestEventDate"] is None or created_str > comp_map[comp_id]["latestEventDate"]):
                    comp_map[comp_id]["latestEventDate"] = created_str
                    comp_map[comp_id]["latestEvent"] = etype

        by_comp = list(comp_map.values())
        by_event = [{"eventType": k, "count": v} for k, v in event_map.items()]

        return {
            "totalDocuments": total_docs,
            "documentsThisWeek": docs_this_week,
            "criticalEvents": critical,
            "highEvents": high,
            "mediumEvents": medium,
            "lowEvents": low,
            "byCompetitor": by_comp,
            "byEventType": by_event,
        }
    except Exception as exc:
        logger.exception("Failed to get intelligence stats for %s: %s", company_id, str(exc))
        return {
            "totalDocuments": 0,
            "documentsThisWeek": 0,
            "criticalEvents": 0,
            "highEvents": 0,
            "mediumEvents": 0,
            "lowEvents": 0,
            "byCompetitor": [],
            "byEventType": []
        }


def update_company_weekly_summary(company_id: str, data: Dict[str, Any]) -> bool:
    """Update weekly intelligence brief fields on company profile."""
    if not supabase_client:
        return False
    payload = {
        "weekly_brief": data.get("weeklyBrief"),
        "top_threats": data.get("topThreats", []),
        "opportunities": data.get("opportunities", []),
        "watch_list": data.get("watchList", []),
        "strategic_recommendations": data.get("strategicRecommendations", []),
        "competitive_velocity": data.get("competitiveVelocity", []),
        "weekly_brief_generated_at": datetime.utcnow().isoformat(),
    }
    try:
        supabase_client.table("companies").update(payload).eq("id", company_id).execute()
        return True
    except Exception as exc:
        logger.exception("Failed to update company weekly summary for %s: %s", company_id, str(exc))
        return False


def get_completed_companies() -> list[Dict[str, Any]]:
    """Return all companies that have setup completed."""
    if not supabase_client:
        return []
    try:
        res = (
            supabase_client.table("companies")
            .select("*")
            .or_("setup_status.eq.COMPLETED,onboarding_completed.eq.true")
            .execute()
        )
        return res.data if res and res.data else []
    except Exception as exc:
        logger.exception("Failed to get completed companies: %s", str(exc))
        return []


# ---------------------------------------------------------------------------
# Task Management (Action Center) Helpers
# ---------------------------------------------------------------------------

def get_tasks(
    company_id: str,
    status: Optional[str] = "active",
    priority: Optional[str] = None,
    category: Optional[str] = None,
    competitor_id: Optional[str] = None,
    source_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> tuple[list[Dict[str, Any]], Dict[str, int]]:
    """Fetch tasks and return stats."""
    if not supabase_client:
        return [], {}

    try:
        query = supabase_client.table("tasks").select("*", count="exact").eq("company_id", company_id)

        if status:
            if status == "active":
                query = query.in_("status", ["TODO", "IN_PROGRESS"])
            else:
                query = query.eq("status", status)

        if priority:
            query = query.eq("priority", priority)
        if category:
            query = query.eq("category", category)
        if competitor_id:
            query = query.eq("competitor_id", competitor_id)
        if source_type:
            query = query.eq("source_type", source_type)

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        res = query.execute()
        tasks = res.data if res and res.data else []
        total = res.count if res and res.count is not None else len(tasks)

        # Get counts for all active tasks to fulfill stats requirements
        stats_query = supabase_client.table("tasks").select("status, priority").eq("company_id", company_id).execute()
        all_tasks = stats_query.data if stats_query and stats_query.data else []

        stats = {
            "total": total,
            "todo": sum(1 for t in all_tasks if t.get("status") == "TODO"),
            "inProgress": sum(1 for t in all_tasks if t.get("status") == "IN_PROGRESS"),
            "done": sum(1 for t in all_tasks if t.get("status") == "DONE"),
            "dismissed": sum(1 for t in all_tasks if t.get("status") == "DISMISSED"),
            "critical": sum(1 for t in all_tasks if t.get("priority") == "CRITICAL" and t.get("status") in ("TODO", "IN_PROGRESS")),
            "high": sum(1 for t in all_tasks if t.get("priority") == "HIGH" and t.get("status") in ("TODO", "IN_PROGRESS")),
            "medium": sum(1 for t in all_tasks if t.get("priority") == "MEDIUM" and t.get("status") in ("TODO", "IN_PROGRESS")),
            "low": sum(1 for t in all_tasks if t.get("priority") == "LOW" and t.get("status") in ("TODO", "IN_PROGRESS"))
        }

        return tasks, stats
    except Exception as exc:
        logger.exception("Failed to get tasks for company %s: %s", company_id, str(exc))
        return [], {}


def create_task(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not supabase_client:
        return None
    try:
        res = supabase_client.table("tasks").insert(payload).execute()
        return res.data[0] if res and res.data else None
    except Exception as exc:
        logger.exception("Failed to create task: %s", str(exc))
        return None


def update_task(task_id: str, company_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not supabase_client or not payload:
        return None
    try:
        payload["updated_at"] = datetime.utcnow().isoformat()
        res = supabase_client.table("tasks").update(payload).eq("id", task_id).eq("company_id", company_id).execute()
        return res.data[0] if res and res.data else None
    except Exception as exc:
        logger.exception("Failed to update task %s: %s", task_id, str(exc))
        return None


def delete_task(task_id: str, company_id: str) -> bool:
    if not supabase_client:
        return False
    try:
        supabase_client.table("tasks").delete().eq("id", task_id).eq("company_id", company_id).execute()
        return True
    except Exception as exc:
        logger.exception("Failed to delete task %s: %s", task_id, str(exc))
        return False


def get_task_by_id(task_id: str, company_id: str) -> Optional[Dict[str, Any]]:
    if not supabase_client:
        return None
    try:
        res = supabase_client.table("tasks").select("*").eq("id", task_id).eq("company_id", company_id).execute()
        return res.data[0] if res and res.data else None
    except Exception as exc:
        logger.exception("Failed to fetch task %s: %s", task_id, str(exc))
        return None


def get_task_stats(company_id: str) -> Dict[str, Any]:
    if not supabase_client:
        return {}
    try:
        now = datetime.utcnow()
        week_ago = (now - timedelta(days=7)).isoformat()
        
        # We need to fetch all tasks to calculate overdue properly because date comparisons in supabase can be tricky
        res = supabase_client.table("tasks").select("*").eq("company_id", company_id).execute()
        tasks = res.data if res and res.data else []

        total_active = 0
        critical = 0
        high = 0
        overdue = 0
        completed_this_week = 0
        generated_this_week = 0

        for t in tasks:
            status = t.get("status")
            priority = t.get("priority")
            source_type = t.get("source_type")
            due_date_str = t.get("due_date")
            completed_at_str = t.get("completed_at")
            created_at_str = t.get("created_at")

            if status in ("TODO", "IN_PROGRESS"):
                total_active += 1
                if priority == "CRITICAL":
                    critical += 1
                elif priority == "HIGH":
                    high += 1
                
                if due_date_str:
                    due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    if due_date < now:
                        overdue += 1

            if status == "DONE" and completed_at_str:
                if completed_at_str >= week_ago:
                    completed_this_week += 1

            if source_type == "AI_GENERATED" and created_at_str:
                if created_at_str >= week_ago:
                    generated_this_week += 1

        return {
            "totalActive": total_active,
            "critical": critical,
            "high": high,
            "overdue": overdue,
            "completedThisWeek": completed_this_week,
            "generatedThisWeek": generated_this_week
        }
    except Exception as exc:
        logger.exception("Failed to get task stats for %s: %s", company_id, str(exc))
        return {}


def check_task_exists_for_source(source_column: str, source_id: str) -> bool:
    if not supabase_client:
        return False
    try:
        res = supabase_client.table("tasks").select("id").eq(source_column, source_id).limit(1).execute()
        return len(res.data) > 0 if res and res.data else False
    except Exception as exc:
        logger.exception("Failed to check task exists for %s %s: %s", source_column, source_id, str(exc))
        return False


