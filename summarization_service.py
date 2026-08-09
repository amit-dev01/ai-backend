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

        # Fetch intelligence documents from the past 7 days (limit 50 to avoid massive context window)
        docs = get_recent_intelligence_documents(company_id, days=7, limit=50)
        
        if not docs:
            logger.info("No recent intelligence documents found for company %s. Skipping brief generation.", company_id)
            return

        logger.info("Fetched %d recent documents for summarization.", len(docs))

        # Format documents into a context block
        docs_context = ""
        for i, doc in enumerate(docs):
            docs_context += f"Document {i+1}:\n"
            docs_context += f"- Competitor: {doc.get('competitor_name', 'Unknown')}\n"
            docs_context += f"- Title: {doc.get('title', '')}\n"
            docs_context += f"- Summary: {doc.get('summary', '')}\n"
            docs_context += f"- Event Type: {doc.get('event_type', '')}\n"
            docs_context += f"- Impact Label: {doc.get('impact_label', '')}\n\n"

        prompt = f"""You are a world-class competitive intelligence analyst. You are writing an automated executive Strategy Brief for the company '{company.get('company_name', 'Our Company')}'.
        
Below are the recent intelligence documents collected about their competitors over the last 7 days.
Analyze this data and synthesize it into a strategic brief.

Return ONLY a valid JSON object with the following exact keys (no markdown formatting, no explanations):
- "weekly_brief": A 2-3 sentence high-level summary of the most critical competitor movements this week.
- "top_threats": A list of up to 3 objects. Each object must have: "threat" (string), "competitor" (string), "urgency" (string, HIGH/MEDIUM/LOW), "recommendedAction" (string).
- "opportunities": A list of up to 3 objects. Each object must have: "opportunity" (string), "basis" (string), "recommendedAction" (string).
- "watch_list": A list of up to 3 competitor names (strings) that are highly active right now.
- "strategic_recommendations": A list of 3 highly actionable strategic recommendations based ONLY on the provided events.

Recent Intelligence Data:
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
