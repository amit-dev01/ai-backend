import json
import logging
import asyncio
from datetime import datetime
from typing import Any, Dict

from database import (
    supabase_client,
    get_recent_intelligence_documents,
    get_company_profile_by_id,
    insert_audit_log
)
from config import EXTRACTION_MODEL, LLM_MODEL
from discovery_service import _call_groq_json  # We can reuse the Groq JSON calling method with retries

logger = logging.getLogger(__name__)

async def generate_strategy_brief(company_id: str) -> None:
    """Generate the weekly AI strategy brief using Groq and save it to the DB."""
    logger.info("=== Starting AI Strategy Brief Generation for Company %s ===", company_id)
    
    try:
        # Fetch company context
        company = get_company_profile_by_id(company_id)
        if not company:
            logger.error("Company not found.")
            return

        # Fetch intelligence documents from the past 30 days (richer context for strategic briefs)
        docs = get_recent_intelligence_documents(company_id, days=30, limit=50)
        
        if not docs:
            logger.info("No recent intelligence documents found for company %s. Skipping brief generation.", company_id)
            return

        logger.info("Fetched %d recent documents (last 30 days) for summarization.", len(docs))

        # Format documents into a rich structured context block
        docs_context = ""
        for i, doc in enumerate(docs):
            docs_context += f"Document {i+1}:\n"
            docs_context += f"- Competitor: {doc.get('competitor_name', 'Unknown')}\n"
            docs_context += f"- Title: {doc.get('title', '')}\n"
            docs_context += f"- Event Type: {doc.get('event_type', '')}\n"
            docs_context += f"- Summary: {doc.get('summary', '')}\n"
            docs_context += f"- Impact: {doc.get('impact_score', 0)}/100 ({doc.get('impact_label', '')})\n"
            docs_context += f"- Relevance: {doc.get('relevance_score', 0)}/100\n"
            if doc.get('relevance_reason'):
                docs_context += f"- Why it matters for us: {doc.get('relevance_reason')}\n"
            docs_context += "\n"

        prompt = f"""You are a world-class competitive intelligence analyst writing an automated executive Strategy Brief for '{company.get('company_name', 'Our Company')}' in the {company.get('industry', 'market')}.
        
Below are {len(docs)} intelligence events from the past 30 days. Produce a concise, highly actionable strategic brief.
Reference specific competitor names and events — no generic advice.

Return ONLY a valid JSON object (no markdown, no explanations) with these exact keys:
- "weekly_brief": 4-5 sentence strategic narrative. Lead with the most critical development. Name competitors. End with the single most urgent action.
- "top_threats": List of up to 3 objects, each with: "threat" (specific, name the competitor), "competitor" (name), "urgency" (HIGH/MEDIUM/LOW), "recommendedAction" (verb + deliverable).
- "opportunities": List of up to 3 objects, each with: "opportunity" (specific gap), "basis" (event that makes this possible), "recommendedAction" (specific next step).
- "watch_list": List of up to 4 competitor names most active in this period.
- "strategic_recommendations": List of 3-4 objects, each with: "recommendation" (specific action), "priority" (P0 this week / P1 this month / P2 this quarter), "rationale" (one sentence tied to data), "owner" (Marketing/Product/Sales/Founders/Engineering).

Recent Intelligence Data (last 30 days):
{docs_context}
"""

        logger.info("Sending strategy brief prompt to Groq...")
        
        # We use LLM_MODEL (usually 70b) instead of extraction model since this requires deep reasoning
        raw_json = await _call_groq_json(prompt, model=LLM_MODEL)
        
        if not raw_json or not isinstance(raw_json, dict):
            logger.error("Failed to generate valid JSON from Groq for strategy brief.")
            return
            
        # Ensure fallback for missing keys
        brief_data = {
            "weekly_brief": raw_json.get("weekly_brief", "No significant activity detected this week."),
            "top_threats": raw_json.get("top_threats", []),
            "opportunities": raw_json.get("opportunities", []),
            "watch_list": raw_json.get("watch_list", []),
            "strategic_recommendations": raw_json.get("strategic_recommendations", []),
            "weekly_brief_generated_at": datetime.utcnow().isoformat()
        }

        # Save to database
        logger.info("Saving generated strategy brief to database...")
        supabase_client.table("companies").update(brief_data).eq("id", company_id).execute()
        
        # Log the action
        insert_audit_log(
            company_id=company_id,
            user_id=company.get("owner_id"),
            action="GENERATED_STRATEGY_BRIEF",
            entity_type="COMPANY",
            entity_id=company_id,
            metadata={"document_count": len(docs)}
        )

        logger.info("=== Strategy Brief Generation Completed Successfully ===")

    except Exception as exc:
        logger.exception("Failed to generate strategy brief for %s: %s", company_id, str(exc))
