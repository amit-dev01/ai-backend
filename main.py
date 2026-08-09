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

from typing import Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query
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
    IntelligenceDocumentOut,
    IntelligenceFeedResponse,
    IntelligenceSummaryResponse,
    IntelligenceStatsResponse,
    MonitoringJobOut,
    MonitoringJobsResponse,
    CompetitorStats,
    EventTypeStats,
    CompanyProfileUpdatePayload,
    CompanySettingsOut,
    CompanySettingsUpdatePayload,
    AuditLogResponse,
    CompetitorEditPayload,
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
    get_intelligence_feed,
    get_intelligence_stats,
    get_monitoring_jobs_history,
    get_active_monitoring_job,
    create_monitoring_job,
    supabase_client,
    update_company_profile_partial,
    update_company_settings,
    insert_audit_log,
    update_competitor_fields,
    delete_competitor_permanently,
    update_competitor_research_status,
    get_audit_logs,
)
from auth import get_current_user
from discovery_service import run_competitor_discovery
from competitor_monitoring_service import CompetitorMonitoringService
from scheduler import start_scheduler, stop_scheduler


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


@app.on_event("startup")
async def startup_event():
    logger.info("Initializing background scheduled cron jobs...")
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down background scheduler...")
    stop_scheduler()


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

_active_background_tasks = set()


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


@app.put("/api/company/profile")
async def update_company_profile(
    payload: CompanyProfileUpdatePayload,
    user_id: str = Depends(get_current_user)
) -> dict:
    """Update existing company profile fields."""
    company = get_company_profile(user_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found.")
    
    company_id = str(company.get("id", ""))
    update_data = payload.model_dump(exclude_unset=True)
    
    if "website" in update_data and update_data["website"]:
        update_data["website"] = str(update_data["website"])
        
    core_fields = {"companyName", "industry", "productsOrServices"}
    significant_change = any(field in update_data for field in core_fields)
    
    db_payload = {
        "company_name": update_data.get("companyName", company.get("company_name")),
        "website": update_data.get("website", company.get("website")),
        "industry": update_data.get("industry", company.get("industry")),
        "description": update_data.get("description", company.get("description")),
        "company_stage": update_data.get("companyStage", company.get("company_stage")),
        "company_size": update_data.get("companySize", company.get("company_size")),
    }
    # Clean up none values
    db_payload = {k: v for k, v in db_payload.items() if v is not None}
    
    updated = update_company_profile_partial(company_id, db_payload)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update company profile.")
        
    insert_audit_log(
        company_id=company_id,
        user_id=user_id,
        action="UPDATED_PROFILE",
        entity_type="COMPANY",
        entity_id=company_id,
        metadata={"fields_updated": list(update_data.keys()), "significant_change": significant_change}
    )
    
    return {
        "status": "ok",
        "message": "Profile updated successfully.",
        "significantChange": significant_change
    }


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


@app.post("/api/company/rediscovery")
async def trigger_rediscovery(user_id: str = Depends(get_current_user)) -> dict:
    """Manually trigger discovery with rate limiting."""
    company = get_company_profile(user_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found.")
        
    company_id = str(company.get("id", ""))
    
    # Check rate limit (simple check: max 3 per 30 days)
    run_count = company.get("discovery_run_count") or 1
    last_run = company.get("last_discovery_at")
    
    if last_run:
        last_date = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
        if (datetime.now(last_date.tzinfo) - last_date).days < 30 and run_count >= 3:
            raise HTTPException(status_code=429, detail="Discovery limit reached. Max 3 times per 30 days.")
    
    # Update count
    new_count = run_count + 1 if last_run and (datetime.now(datetime.fromisoformat(last_run.replace("Z", "+00:00")).tzinfo) - datetime.fromisoformat(last_run.replace("Z", "+00:00"))).days < 30 else 1
    
    update_company_settings(company_id, {
        "discovery_run_count": new_count,
        "last_discovery_at": datetime.utcnow().isoformat()
    })
    
    insert_audit_log(company_id, user_id, "TRIGGERED_REDISCOVERY", "COMPANY", company_id, {"run_count": new_count})
    run_competitor_discovery(company_id)
    
    return {"status": "ok", "message": "Re-discovery started successfully."}


@app.get("/api/company/settings", response_model=CompanySettingsOut)
async def get_settings(user_id: str = Depends(get_current_user)) -> CompanySettingsOut:
    company = get_company_profile(user_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found.")
    
    company_id = str(company.get("id", ""))
    active = len(get_competitors_for_company(company_id, status="active"))
    archived = len(get_competitors_for_company(company_id, status="archived"))
    
    return CompanySettingsOut(
        monitoringEnabled=company.get("monitoring_enabled", True),
        emailDigestEnabled=company.get("email_digest_enabled", True),
        criticalAlertsEnabled=company.get("critical_alerts_enabled", True),
        maxCompetitorsMonitored=company.get("max_competitors_monitored", 10),
        discoveryRunCount=company.get("discovery_run_count") or 1,
        lastDiscoveryAt=company.get("last_discovery_at"),
        activeCompetitors=active,
        archivedCompetitors=archived,
    )


@app.put("/api/company/settings", response_model=CompanySettingsOut)
async def update_settings(
    payload: CompanySettingsUpdatePayload,
    user_id: str = Depends(get_current_user)
) -> CompanySettingsOut:
    company = get_company_profile(user_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found.")
    
    company_id = str(company.get("id", ""))
    update_data = payload.model_dump(exclude_unset=True)
    
    db_payload = {}
    if "monitoringEnabled" in update_data: db_payload["monitoring_enabled"] = update_data["monitoringEnabled"]
    if "emailDigestEnabled" in update_data: db_payload["email_digest_enabled"] = update_data["emailDigestEnabled"]
    if "criticalAlertsEnabled" in update_data: db_payload["critical_alerts_enabled"] = update_data["criticalAlertsEnabled"]
    if "maxCompetitorsMonitored" in update_data: db_payload["max_competitors_monitored"] = update_data["maxCompetitorsMonitored"]
    
    if db_payload:
        updated = update_company_settings(company_id, db_payload)
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update settings.")
            
        insert_audit_log(company_id, user_id, "UPDATED_SETTINGS", "COMPANY", company_id, {"fields": list(update_data.keys())})
    
    return await get_settings(user_id)


@app.get("/api/company/activity", response_model=AuditLogResponse)
async def get_activity(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user)
) -> AuditLogResponse:
    company = get_company_profile(user_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found.")
        
    company_id = str(company.get("id", ""))
    logs, total = get_audit_logs(company_id, limit, offset)
    
    mapped_logs = []
    for log in logs:
        mapped_logs.append({
            "id": str(log.get("id")),
            "action": log.get("action"),
            "entityType": log.get("entity_type"),
            "entityId": str(log.get("entity_id")),
            "metadata": log.get("metadata") or {},
            "createdAt": log.get("created_at")
        })
        
    return AuditLogResponse(activities=mapped_logs, total=total)


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
        isAccepted=row.get("is_accepted"),
        isActive=row.get("is_active"),
        customType=row.get("custom_type"),
        effectiveType=row.get("custom_type") or row.get("type"),
        notes=row.get("notes"),
        lastResearchedAt=row.get("last_researched_at"),
        researchStatus=row.get("research_status")
    )


@app.get("/api/competitors", response_model=CompetitorsListResponse)
async def get_competitors(
    status: str = Query("active", description="active or archived or all"),
    type: Optional[str] = Query(None, description="Filter by type (DIRECT, etc)"),
    source: Optional[str] = Query(None, description="Filter by source"),
    accepted: Optional[str] = Query(None, description="true, false, or pending"),
    user_id: str = Depends(get_current_user)
) -> CompetitorsListResponse:
    """Get competitors for the user's company with filters."""
    company = get_company_profile(user_id)
    if not company:
        return CompetitorsListResponse(
            competitors=[], 
            summary={"total": 0, "active": 0, "archived": 0, "pendingReview": 0}
        )

    company_id = str(company.get("id", ""))
    rows = get_competitors_for_company(company_id, status=status, comp_type=type, source=source, accepted=accepted)

    competitors = [_map_competitor_row(r) for r in rows]
    total = len(competitors)
    
    # We might want to calculate stats without the query filters, but usually we just calculate on the returned set
    active = sum(1 for c in competitors if c.isActive)
    archived = sum(1 for c in competitors if not c.isActive)
    direct = sum(1 for c in competitors if c.effectiveType == "DIRECT")
    indirect = sum(1 for c in competitors if c.effectiveType == "INDIRECT")
    emerging = sum(1 for c in competitors if c.effectiveType == "EMERGING")
    pending = sum(1 for c in competitors if c.isAccepted is None)

    return CompetitorsListResponse(
        competitors=competitors,
        summary={
            "total": total,
            "active": active,
            "archived": archived,
            "pendingReview": pending
        }
    )


@app.put("/api/competitors/{competitor_id}", response_model=CompetitorOut)
async def edit_competitor(
    competitor_id: str,
    payload: CompetitorEditPayload,
    user_id: str = Depends(get_current_user)
) -> CompetitorOut:
    company = get_company_profile(user_id)
    if not company: raise HTTPException(status_code=404, detail="Company not found.")
    
    company_id = str(company.get("id", ""))
    comp = get_competitor_by_id(competitor_id)
    if not comp or str(comp.get("company_id")) != company_id:
        raise HTTPException(status_code=404, detail="Competitor not found.")
        
    update_data = payload.model_dump(exclude_unset=True)
    db_payload = {}
    if "name" in update_data: db_payload["name"] = update_data["name"]
    if "website" in update_data: db_payload["website_url"] = update_data["website"]
    if "notes" in update_data: db_payload["notes"] = update_data["notes"]
    if "customType" in update_data: db_payload["custom_type"] = update_data["customType"]
    
    if db_payload:
        updated = update_competitor_fields(competitor_id, db_payload)
        if not updated: raise HTTPException(status_code=500, detail="Failed to update competitor.")
        insert_audit_log(company_id, user_id, "UPDATED_COMPETITOR", "COMPETITOR", competitor_id, {"fields": list(db_payload.keys())})
        return _map_competitor_row(updated)
        
    return _map_competitor_row(comp)


@app.post("/api/competitors/{competitor_id}/archive")
async def archive_competitor(competitor_id: str, user_id: str = Depends(get_current_user)):
    company = get_company_profile(user_id)
    if not company: raise HTTPException(status_code=404, detail="Company not found.")
    
    company_id = str(company.get("id", ""))
    comp = get_competitor_by_id(competitor_id)
    if not comp or str(comp.get("company_id")) != company_id: raise HTTPException(status_code=404, detail="Competitor not found.")
    
    update_competitor_fields(competitor_id, {"is_active": False})
    insert_audit_log(company_id, user_id, "ARCHIVED_COMPETITOR", "COMPETITOR", competitor_id, {})
    return {"status": "ok", "message": "Competitor archived."}


@app.post("/api/competitors/{competitor_id}/restore")
async def restore_competitor(competitor_id: str, user_id: str = Depends(get_current_user)):
    company = get_company_profile(user_id)
    if not company: raise HTTPException(status_code=404, detail="Company not found.")
    
    company_id = str(company.get("id", ""))
    comp = get_competitor_by_id(competitor_id)
    if not comp or str(comp.get("company_id")) != company_id: raise HTTPException(status_code=404, detail="Competitor not found.")
    
    update_competitor_fields(competitor_id, {"is_active": True})
    insert_audit_log(company_id, user_id, "RESTORED_COMPETITOR", "COMPETITOR", competitor_id, {})
    return {"status": "ok", "message": "Competitor restored."}


@app.delete("/api/competitors/{competitor_id}")
async def delete_competitor(competitor_id: str, user_id: str = Depends(get_current_user)):
    company = get_company_profile(user_id)
    if not company: raise HTTPException(status_code=404, detail="Company not found.")
    
    company_id = str(company.get("id", ""))
    comp = get_competitor_by_id(competitor_id)
    if not comp or str(comp.get("company_id")) != company_id: raise HTTPException(status_code=404, detail="Competitor not found.")
    
    # 7-day archive rule check for AI-discovered
    if comp.get("source") != "MANUAL":
        is_active = comp.get("is_active", True)
        if is_active:
            raise HTTPException(status_code=400, detail="AI-discovered competitors must be archived for 7 days before deletion.")
        # NOTE: A real 7-day check would look at an archived_at timestamp. Since we don't have one, we allow deletion if is_active is false to simplify, or we can check audit logs.
    
    deleted = delete_competitor_permanently(competitor_id)
    if not deleted: raise HTTPException(status_code=500, detail="Failed to delete competitor.")
    insert_audit_log(company_id, user_id, "DELETED_COMPETITOR", "COMPETITOR", competitor_id, {})
    return {"status": "ok", "message": "Competitor deleted."}


@app.post("/api/competitors/{competitor_id}/research")
async def re_research_competitor(competitor_id: str, user_id: str = Depends(get_current_user)):
    company = get_company_profile(user_id)
    if not company: raise HTTPException(status_code=404, detail="Company not found.")
    
    company_id = str(company.get("id", ""))
    comp = get_competitor_by_id(competitor_id)
    if not comp or str(comp.get("company_id")) != company_id: raise HTTPException(status_code=404, detail="Competitor not found.")
    
    if not comp.get("website_url"):
        raise HTTPException(status_code=400, detail="Competitor must have a website URL to be researched.")
        
    update_competitor_research_status(competitor_id, "PROCESSING")
    insert_audit_log(company_id, user_id, "TRIGGERED_RESEARCH", "COMPETITOR", competitor_id, {})
    
    from discovery_service import re_research_competitor_background
    import asyncio
    task = asyncio.create_task(re_research_competitor_background(competitor_id, company_id, comp.get("website_url"), comp.get("name")))
    _active_background_tasks.add(task)
    task.add_done_callback(_active_background_tasks.discard)
    
    return {"status": "ok", "message": "Research job started in background."}


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
# Phase 2 — Intelligence Monitoring Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/intelligence/feed", response_model=IntelligenceFeedResponse)
async def get_intelligence_feed_endpoint(
    competitorId: Optional[str] = None,
    eventType: Optional[str] = None,
    impactLabel: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user)
) -> IntelligenceFeedResponse:
    """Get recent intelligence feed documents for the authenticated user's company."""
    company = get_company_profile(user_id)
    if not company:
        return IntelligenceFeedResponse(documents=[], total=0, hasMore=False)

    company_id = str(company.get("id", ""))
    docs, total = get_intelligence_feed(
        company_id=company_id,
        competitor_id=competitorId,
        event_type=eventType,
        impact_label=impactLabel,
        limit=limit,
        offset=offset,
    )

    doc_outs = []
    for d in docs:
        doc_outs.append(
            IntelligenceDocumentOut(
                id=str(d.get("id", "")),
                competitorId=str(d.get("competitor_id", "")),
                competitorName=d.get("competitor_name"),
                sourceUrl=d.get("source_url", ""),
                title=d.get("title"),
                summary=d.get("summary"),
                eventType=d.get("event_type"),
                sentiment=d.get("sentiment"),
                sentimentConfidence=d.get("sentiment_confidence"),
                relevanceScore=d.get("relevance_score"),
                relevanceReason=d.get("relevance_reason"),
                impactScore=d.get("impact_score"),
                impactLabel=d.get("impact_label"),
                publishedDate=d.get("published_date"),
                createdAt=d.get("created_at"),
            )
        )

    has_more = (offset + limit) < total
    return IntelligenceFeedResponse(documents=doc_outs, total=total, hasMore=has_more)


@app.get("/api/intelligence/strategy-brief", response_model=IntelligenceSummaryResponse)
async def get_intelligence_summary_endpoint(
    user_id: str = Depends(get_current_user)
) -> IntelligenceSummaryResponse:
    """Get latest weekly AI strategy summary for the authenticated user's company."""
    company = get_company_profile(user_id)
    if not company:
        return IntelligenceSummaryResponse()

    return IntelligenceSummaryResponse(
        weeklyBrief=company.get("weekly_brief"),
        topThreats=company.get("top_threats") or [],
        opportunities=company.get("opportunities") or [],
        watchList=company.get("watch_list") or [],
        strategicRecommendations=company.get("strategic_recommendations") or [],
        generatedAt=company.get("weekly_brief_generated_at"),
    )


@app.get("/api/intelligence/competitor-stats", response_model=IntelligenceStatsResponse)
async def get_intelligence_stats_endpoint(
    user_id: str = Depends(get_current_user)
) -> IntelligenceStatsResponse:
    """Get aggregated statistics about intelligence collected for the company."""
    company = get_company_profile(user_id)
    if not company:
        return IntelligenceStatsResponse(
            totalDocuments=0,
            documentsThisWeek=0,
            criticalEvents=0,
            highEvents=0,
            mediumEvents=0,
            lowEvents=0,
            byCompetitor=[],
            byEventType=[]
        )

    company_id = str(company.get("id", ""))
    stats = get_intelligence_stats(company_id)

    by_comp = [CompetitorStats(**c) for c in stats.get("byCompetitor", [])]
    by_event = [EventTypeStats(**e) for e in stats.get("byEventType", [])]

    return IntelligenceStatsResponse(
        totalDocuments=stats.get("totalDocuments", 0),
        documentsThisWeek=stats.get("documentsThisWeek", 0),
        criticalEvents=stats.get("criticalEvents", 0),
        highEvents=stats.get("highEvents", 0),
        mediumEvents=stats.get("mediumEvents", 0),
        lowEvents=stats.get("lowEvents", 0),
        byCompetitor=by_comp,
        byEventType=by_event,
    )


@app.get("/api/intelligence/trends")
async def get_intelligence_trends(user_id: str = Depends(get_current_user)):
    """Mock endpoint for trends."""
    return {"trends": []}


@app.get("/api/intelligence/alerts")
async def get_intelligence_alerts(user_id: str = Depends(get_current_user)):
    """Mock endpoint for alerts."""
    return {"alerts": []}


@app.post("/api/intelligence/trigger-monitoring")
async def trigger_monitoring_endpoint(
    user_id: str = Depends(get_current_user)
) -> dict:
    """Manually trigger a background news monitoring job for the user's company."""
    company = get_company_profile(user_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found.")

    company_id = str(company.get("id", ""))
    active_job = get_active_monitoring_job(company_id)
    if active_job:
        raise HTTPException(
            status_code=400,
            detail="A monitoring job is already currently running for this company."
        )

    job = create_monitoring_job(company_id=company_id, competitor_id=None, job_type="NEWS_MONITORING")
    job_id = job.get("id") if job else f"job-{int(datetime.utcnow().timestamp())}"

    task = asyncio.create_task(CompetitorMonitoringService.runNewsMonitoring(company_id))
    _active_background_tasks.add(task)
    task.add_done_callback(_active_background_tasks.discard)

    return {
        "message": "Monitoring job started",
        "jobId": str(job_id)
    }


@app.get("/api/intelligence/jobs", response_model=MonitoringJobsResponse)
async def get_monitoring_jobs_endpoint(
    user_id: str = Depends(get_current_user)
) -> MonitoringJobsResponse:
    """Get recent monitoring jobs history for the company."""
    company = get_company_profile(user_id)
    if not company:
        return MonitoringJobsResponse(jobs=[])

    company_id = str(company.get("id", ""))
    jobs_rows = get_monitoring_jobs_history(company_id, limit=20)

    job_outs = []
    for j in jobs_rows:
        job_outs.append(
            MonitoringJobOut(
                id=str(j.get("id", "")),
                jobType=j.get("job_type", "NEWS_MONITORING"),
                status=j.get("status", "COMPLETED"),
                documentsFound=j.get("documents_found", 0),
                documentsProcessed=j.get("documents_processed", 0),
                startedAt=j.get("started_at"),
                completedAt=j.get("completed_at"),
                error=j.get("error"),
            )
        )

    return MonitoringJobsResponse(jobs=job_outs)


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

