"""
IntelligenceSummaryService for Phase 2 Live Competitor Monitoring.

Generates AI-powered strategic intelligence briefs summarizing top competitive
developments, threats, opportunities, competitive velocity, and recommendations.
Uses the last 30 days of intelligence documents (vs. 7 days previously) for
richer context.
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
    """Service generating AI strategic summaries from collected intelligence."""

    @staticmethod
    async def generateWeeklySummary(company_id: str) -> Optional[dict]:
        """Generate strategic AI intelligence brief and save to company record.

        Uses last 30 days of documents (up to 50) for rich competitive context.
        Produces: weekly brief, top threats, opportunities, watch list,
        competitive velocity ranking, and strategic recommendations.
        """
        logger.info("=== Generating AI Intelligence Brief for Company ID: %s ===", company_id)

        try:
            company = get_company_profile_by_id(company_id)
            if not company:
                logger.error("Company profile not found for ID %s", company_id)
                return None

            company_name = company.get("company_name", "Our Company")
            industry = company.get("industry", "Market Segment")
            description = company.get("description", "")
            products_raw = company.get("products_or_services", [])
            products_str = ", ".join(products_raw) if isinstance(products_raw, list) else str(products_raw)

            competitors = get_accepted_competitors_for_company(company_id)
            comp_lines = []
            for c in competitors:
                line = (
                    f"- {c.get('name', 'Competitor')} "
                    f"(Type: {c.get('type', 'DIRECT')}, "
                    f"Score: {c.get('competitive_score', 50)}/100, "
                    f"Model: {c.get('business_model', 'Unknown')})"
                )
                comp_lines.append(line)
            comp_str = "\n".join(comp_lines) if comp_lines else "No accepted competitors yet."

            # Fetch last 30 days — gives much richer context for strategic briefs
            docs = get_recent_intelligence_documents(company_id, days=30, limit=50)

            if not docs:
                logger.info("No recent intelligence documents found for company %s — using minimal brief.", company_id)
                fallback = _build_fallback_brief(company_name, competitors)
                update_company_weekly_summary(company_id, fallback)
                return fallback

            # Build rich document context with all key fields
            doc_lines = []
            competitor_activity: dict[str, int] = {}
            for d in docs:
                comp_nm = d.get("competitor_name") or "Competitor"
                competitor_activity[comp_nm] = competitor_activity.get(comp_nm, 0) + 1
                evt = d.get("event_type", "OTHER")
                sub = d.get("sub_type") or ""
                imp_label = d.get("impact_label", "MEDIUM")
                imp_score = d.get("impact_score", 50)
                sent = d.get("sentiment", "NEUTRAL")
                relevance = d.get("relevance_score", 50)
                summary_text = d.get("summary", "")
                relevance_reason = d.get("relevance_reason", "")
                doc_lines.append(
                    f"- [{comp_nm}] {evt}{' (' + sub + ')' if sub else ''} | "
                    f"Impact: {imp_score}/100 ({imp_label}) | Sentiment: {sent} | Relevance: {relevance}/100\n"
                    f"  Summary: {summary_text}\n"
                    f"  Why it matters for us: {relevance_reason}"
                )

            events_str = "\n".join(doc_lines)

            # Competitive velocity: rank by activity count in last 30 days
            velocity_ranked = sorted(competitor_activity.items(), key=lambda x: x[1], reverse=True)
            velocity_str = ", ".join(f"{name} ({count} events)" for name, count in velocity_ranked[:5])

            # Gather cross-engine intelligence signals
            engine_signals = []
            try:
                from positioning_engine import PositioningEngine
                radar_data = PositioningEngine.get_positioning_radar(company_id)
                engine_signals.append(f"Spatial Encroachment: {radar_data.get('strategicPositioningSummary', '')}")
            except Exception:
                pass

            try:
                from pricing_matrix_service import PricingMatrixService
                p_data = PricingMatrixService.get_category_pricing_matrix(company_id)
                bms = p_data.get("categoryBenchmarks", {})
                p_str = f"Pricing Benchmarks: Floor ${bms.get('marketFloorMinima') or 'N/A'}/mo | Median ${bms.get('categoryMedian') or 'N/A'}/mo | Ceiling ${bms.get('marketCeilingMaxima') or 'N/A'}/mo. {p_data.get('strategicRecommendation', '')}"
                engine_signals.append(p_str)
            except Exception:
                pass

            try:
                from win_loss_service import WinLossService
                d_data = WinLossService.get_deal_analytics(company_id)
                if d_data.get("totalDealsLogged", 0) > 0:
                    engine_signals.append(f"Sales Win/Loss: Win Rate {d_data.get('overallWinRate')}% | Pipeline Lost: ${d_data.get('pipelineLost'):,.0f}. {d_data.get('strategicRecommendation')}")
            except Exception:
                pass

            try:
                from share_of_voice_service import ShareOfVoiceService
                s_data = ShareOfVoiceService.get_category_share_of_voice(company_id)
                engine_signals.append(f"Share of Voice: Buzz Leader is '{s_data.get('categoryBuzzLeader')}'. Our Voice: {s_data.get('ourShareOfVoice')}%.")
            except Exception:
                pass

            engine_signals_str = "\n".join(f"- {s}" for s in engine_signals)

            brief_prompt = f"""You are a Principal Competitive Intelligence Analyst. You have access to {len(docs)} intelligence events from the past 30 days and quantitative market analytics for the company below. Produce a comprehensive, executive-grade strategic brief.
Return ONLY valid JSON — no markdown, no explanation.

OUR COMPANY:
Name: {company_name}
Industry: {industry}
Description: {description}
Products/Services: {products_str}

OUR COMPETITORS (accepted):
{comp_str}

COMPETITIVE VELOCITY (most active in last 30 days):
{velocity_str}

QUANTITATIVE SIGNALS (Positioning, Pricing, Win/Loss, Share of Voice):
{engine_signals_str}

INTELLIGENCE EVENTS (last 30 days, ordered by impact):
{events_str}

Return this exact JSON structure:
{{
  "weeklyBrief": "5-6 sentence strategic narrative. Lead with the single most important development. Cover the competitive landscape shift, what it means for us specifically, and the most urgent action. Be concrete — name competitors and specific events.",
  "topThreats": [
    {{
      "threat": "Specific threat in one clear sentence — name the competitor and the exact action",
      "competitor": "competitor name",
      "urgency": "HIGH or MEDIUM or LOW",
      "evidence": "specific data point or event that supports this threat assessment",
      "recommendedAction": "Specific verb + deliverable, executable this week"
    }}
  ],
  "opportunities": [
    {{
      "opportunity": "Specific competitive gap we can exploit — what is it?",
      "basis": "Which competitor event or weakness makes this possible",
      "potentialImpact": "qualitative description of what winning here means",
      "recommendedAction": "Specific next step, executable this month"
    }}
  ],
  "watchList": ["up to 4 competitor names with highest activity or danger in last 30 days"],
  "competitiveVelocity": [
    {{
      "competitor": "name",
      "eventCount": integer,
      "trend": "Accelerating | Steady | Decelerating",
      "primaryActivity": "what they are mostly doing e.g. product launches, hiring, partnerships"
    }}
  ],
  "strategicRecommendations": [
    {{
      "recommendation": "Specific actionable recommendation — verb + deliverable",
      "priority": "P0 this week | P1 this month | P2 this quarter",
      "rationale": "One sentence tied directly to a specific intelligence event",
      "owner": "Marketing | Product | Sales | Founders | Engineering"
    }}
  ]
}}

Rules:
- Every threat and opportunity must name a specific competitor and reference a specific event.
- Do not include generic recommendations. Each must be triggered by evidence.
- Top threats must be sorted: HIGH urgency first.
- strategicRecommendations: maximum 4, sorted P0 first.
- competitiveVelocity: include only the top 3-4 most active competitors."""

            summary_res = None
            for attempt in range(2):
                try:
                    response = await client.chat.completions.create(
                        model=LLM_MODEL,
                        messages=[{"role": "user", "content": brief_prompt}],
                        response_format={"type": "json_object"} if attempt == 0 else None,
                        temperature=0.25,
                    )
                    raw = response.choices[0].message.content or ""
                    summary_res = _clean_and_parse_json(raw)
                    break
                except Exception as exc:
                    logger.warning("Intelligence brief attempt %d failed: %s", attempt + 1, str(exc))

            if not isinstance(summary_res, dict):
                summary_res = _build_fallback_brief(company_name, competitors)

            update_company_weekly_summary(company_id, summary_res)
            logger.info(
                "Intelligence brief saved for company %s — %d threats, %d opportunities",
                company_id,
                len(summary_res.get("topThreats", [])),
                len(summary_res.get("opportunities", [])),
            )
            return summary_res

        except Exception as exc:
            logger.exception("Failed to generate intelligence brief for company %s: %s", company_id, str(exc))
            return None


def _build_fallback_brief(company_name: str, competitors: list) -> dict:
    """Build a minimal structural fallback when no documents are available."""
    return {
        "weeklyBrief": (
            f"Intelligence monitoring is active for {company_name}. "
            "No significant competitive events have been recorded in the last 30 days. "
            "Run a manual check or wait for the scheduled monitoring job to collect new data."
        ),
        "topThreats": [],
        "opportunities": [],
        "watchList": [c.get("name") for c in competitors[:4] if c.get("name")],
        "competitiveVelocity": [],
        "strategicRecommendations": [
            {
                "recommendation": "Trigger a manual competitive check to collect fresh intelligence",
                "priority": "P0 this week",
                "rationale": "No recent intelligence data available — run a check to populate the feed.",
                "owner": "Founders",
            }
        ],
    }
