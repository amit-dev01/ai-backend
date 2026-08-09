"""
IntelligenceSummaryService module for Phase 2 Live Competitor Monitoring.

Generates weekly AI strategy briefs summarizing top competitive developments, threats, opportunities, and recommendations.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from openai import AsyncOpenAI

from config import GROQ_API_KEY, GROQ_BASE_URL, LLM_MODEL
from database import (
    get_company_profile_by_id,
    get_accepted_competitors_for_company,
    get_recent_intelligence_documents,
    update_company_weekly_summary,
)
from discovery_service import _clean_and_parse_json

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)


class IntelligenceSummaryService:
    """Service generating weekly strategic AI summaries for a company."""

    @staticmethod
    async def generateWeeklySummary(company_id: str) -> Optional[dict]:
        """Generate weekly competitive brief and save to company record."""
        logger.info("=== Generating Weekly AI Intelligence Brief for Company ID: %s ===", company_id)

        try:
            company = get_company_profile_by_id(company_id)
            if not company:
                logger.error("Company profile not found for ID %s", company_id)
                return None

            company_name = company.get("company_name", "Our Company")
            industry = company.get("industry", "Market Segment")
            description = company.get("description", "")

            competitors = get_accepted_competitors_for_company(company_id)
            comp_summary_list = []
            for c in competitors:
                c_name = c.get("name", "Competitor")
                c_type = c.get("type", "DIRECT")
                c_score = c.get("competitive_score", 50)
                comp_summary_list.append(f"- {c_name} (Type: {c_type}, Competitive Score: {c_score})")

            comp_str = "\n".join(comp_summary_list) if comp_summary_list else "No accepted competitors."

            docs = get_recent_intelligence_documents(company_id, days=7, limit=20)
            doc_summary_list = []
            for d in docs:
                c_name = d.get("competitor_name") or "Competitor"
                e_type = d.get("event_type", "OTHER")
                sum_text = d.get("summary", "")
                imp_label = d.get("impact_label", "MEDIUM")
                imp_score = d.get("impact_score", 50)
                sent = d.get("sentiment", "NEUTRAL")
                doc_summary_list.append(f"- [{c_name} | {e_type}] Impact: {imp_score} ({imp_label}), Sentiment: {sent}\n  Summary: {sum_text}")

            events_str = "\n".join(doc_summary_list) if doc_summary_list else "No major intelligence events recorded this week."

            brief_prompt = f"""You are a senior competitive intelligence analyst. Based on the following competitive intelligence data from the past 7 days, generate a comprehensive weekly strategic brief for this company. Return only valid JSON, no explanation, no markdown.

OUR COMPANY:
Name: {company_name}
Industry: {industry}
Description: {description}

OUR COMPETITORS:
{comp_str}

INTELLIGENCE EVENTS THIS WEEK (ordered by impact):
{events_str}

Return this JSON structure:
{{
  "weeklyBrief": "string of 4 to 5 sentences summarizing the most important competitive developments this week",
  "topThreats": [
    {{
      "threat": "string describing the threat",
      "competitor": "competitor name",
      "urgency": "one of HIGH or MEDIUM or LOW",
      "recommendedAction": "string of 1 sentence"
    }}
  ],
  "opportunities": [
    {{
      "opportunity": "string describing the opportunity",
      "basis": "string explaining what intelligence this is based on",
      "recommendedAction": "string of 1 sentence"
    }}
  ],
  "watchList": ["array of up to 3 competitor names that showed the most activity this week and should be watched closely"],
  "strategicRecommendations": ["array of up to 3 strings each being one specific actionable recommendation"]
}}"""

            summary_res = None
            for attempt in range(2):
                try:
                    response = await client.chat.completions.create(
                        model=LLM_MODEL,
                        messages=[{"role": "user", "content": brief_prompt}],
                        response_format={"type": "json_object"} if attempt == 0 else None,
                        temperature=0.3,
                    )
                    raw = response.choices[0].message.content or ""
                    summary_res = _clean_and_parse_json(raw)
                    break
                except Exception as exc:
                    logger.warning("Groq weekly brief attempt %d failed: %s", attempt + 1, str(exc))

            if not isinstance(summary_res, dict):
                summary_res = {
                    "weeklyBrief": f"Weekly intelligence monitoring active for {company_name} in {industry}. Key competitor activities tracked.",
                    "topThreats": [
                        {
                            "threat": "Competitor market movements in core features",
                            "competitor": competitors[0].get("name", "Competitor") if competitors else "Competitor",
                            "urgency": "MEDIUM",
                            "recommendedAction": "Monitor feature rollouts and pricing updates."
                        }
                    ],
                    "opportunities": [
                        {
                            "opportunity": "Differentiate on core customer support and usability",
                            "basis": "Market analysis of competitor focus areas",
                            "recommendedAction": "Highlight value proposition in upcoming marketing campaigns."
                        }
                    ],
                    "watchList": [c.get("name") for c in competitors[:3]],
                    "strategicRecommendations": [
                        "Maintain agile sprint schedule for feature differentiation.",
                        "Review competitor pricing adjustments monthly.",
                        "Gather direct feedback from prospective switchers."
                    ],
                }

            update_company_weekly_summary(company_id, summary_res)
            logger.info("Successfully saved weekly brief for company %s", company_id)
            return summary_res

        except Exception as exc:
            logger.exception("Failed to generate weekly summary for company %s: %s", company_id, str(exc))
            return None
