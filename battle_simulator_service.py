"""
AI Battle Simulator Service.
Game-theoretic outcome simulator for executive scenario planning:
  - "What happens if Competitor X drops prices by 20%?"
  - "What happens if Competitor Y launches an AI Co-Pilot?"
  - "What happens if Competitor Z targets our enterprise accounts with free migration?"
Generates:
  - Numerical risk scores & projected market share displacement
  - Competitor's hidden margin trap / internal vulnerability
  - 3-step Defensive Action Counter-Punch (Immediate 7-day, Mid-term 60-day)
  - Sales Objection Killer script
  - 4-point dynamic timeline forecast
"""

import json
import logging
from typing import Any, Optional
from openai import AsyncOpenAI

from config import GROQ_API_KEY, GROQ_BASE_URL, LLM_MODEL, EXTRACTION_MODEL
from database import get_company_profile_by_id, get_competitor_by_id

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)

SCENARIOS_PRESETS = {
    "PRICE_DROP_20": "Drops core product pricing across all tiers by 20% to trigger price war.",
    "AI_COPILOT_LAUNCH": "Launches an integrated AI copilot claiming to automate 80% of manual workflows.",
    "AGGRESSIVE_BUNDLING": "Bundles their primary paid add-on module for free with enterprise base plans.",
    "ENTERPRISE_DISCOUNT": "Offers 6-month free contract buyout / migration credits targeting our customer base.",
    "OPEN_SOURCE_CORE": "Open-sources their core developer engine under Apache 2.0 to capture developer mindshare.",
}


class BattleSimulatorService:
    """Executes game-theoretic competitive simulations using Groq LLM."""

    @staticmethod
    async def simulate(
        company_id: str,
        competitor_id: str,
        scenario_type: str,
        custom_scenario: Optional[str] = None,
        target_segment: str = "Mid-Market & Enterprise"
    ) -> dict[str, Any]:
        """
        Runs a full scenario simulation against a specific rival.
        """
        company = get_company_profile_by_id(company_id) or {}
        company_name = company.get("company_name", "Our Business")
        industry = company.get("industry", "SaaS")

        competitor = get_competitor_by_id(competitor_id) or {}
        competitor_name = competitor.get("name", "Key Rival")
        threat_score = competitor.get("competitive_score", 65)

        scenario_description = (
            custom_scenario if scenario_type == "CUSTOM" and custom_scenario
            else SCENARIOS_PRESETS.get(scenario_type, "Initiates an aggressive competitive move in our core segment.")
        )

        prompt = f"""You are a Strategic Game Theory & Competitive Simulation Engine.
Analyze the following competitive scenario between our company and our rival:

OUR COMPANY: {company_name} ({industry})
TARGET CUSTOMER SEGMENT: {target_segment}

RIVAL: {competitor_name} (Current Threat Score: {threat_score}/100)
RIVAL MOVE: {competitor_name} {scenario_description}

Perform a rigorous strategic simulation and return ONLY valid JSON matching this exact structure:
{{
  "scenarioTitle": "Short punchy title for this simulated clash",
  "riskLevel": "CRITICAL" or "HIGH" or "MODERATE",
  "riskScore": integer between 35 and 95,
  "projectedMarketShareImpact": "projected percentage shift over 6 months, e.g. -3.8% short-term pipeline risk",
  "competitorVulnerability": "Specific hidden weakness or margin trap this move creates for them (e.g. higher COGS, support bottlenecks, customer resentment)",
  "immediateCounterMeasure": "Specific tactical action our team must take in Days 1 to 7 to neutralize this move",
  "midTermMoatStrategy": "Product, pricing, or ecosystem defense move to deploy in Days 30 to 60",
  "salesRepPlaybook": "Direct word-for-word counter-script sales reps should use when a prospect mentions this competitor move",
  "timelineForecast": [
    {{"phase": "Month 1", "marketImpact": -1.5, "status": "Initial market noise & tire-kickers"}},
    {{"phase": "Month 2", "marketImpact": -3.2, "status": "Peak pricing friction in active deals"}},
    {{"phase": "Month 4", "marketImpact": -1.0, "status": "Stabilization as competitor support strain emerges"}},
    {{"phase": "Month 6", "marketImpact": 1.4, "status": "Net win-back as our product moat takes effect"}}
  ]
}}
"""

        try:
            response = await client.chat.completions.create(
                model=EXTRACTION_MODEL or LLM_MODEL or "qwen/qwen3.8-27b",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=900,
            )
            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)
            
            return {
                "competitorName": competitor_name,
                "scenarioTitle": data.get("scenarioTitle", f"Simulated Clash: {competitor_name}"),
                "riskLevel": data.get("riskLevel", "HIGH"),
                "riskScore": int(data.get("riskScore", 72)),
                "projectedMarketShareImpact": data.get("projectedMarketShareImpact", "-3.5% pipeline exposure"),
                "competitorVulnerability": data.get("competitorVulnerability", "Significantly compresses their gross margins while inflating onboarding overhead."),
                "immediateCounterMeasure": data.get("immediateCounterMeasure", "Launch a value-differentiation one-pager highlighting enterprise SLAs and security compliance."),
                "midTermMoatStrategy": data.get("midTermMoatStrategy", "Introduce an automated workflow tier that eliminates the need for their manual add-on."),
                "salesRepPlaybook": data.get("salesRepPlaybook", f"\"While {competitor_name} is discounting heavily, ask yourself why they need to cut price: look at their lack of enterprise SLA and data guarantees.\""),
                "timelineForecast": data.get("timelineForecast", [
                    {"phase": "Month 1", "marketImpact": -1.5, "status": "Initial noise"},
                    {"phase": "Month 2", "marketImpact": -2.8, "status": "Deal friction"},
                    {"phase": "Month 4", "marketImpact": -0.8, "status": "Counter-action deployed"},
                    {"phase": "Month 6", "marketImpact": 1.2, "status": "Net positive recovery"}
                ])
            }
        except Exception as exc:
            logger.error("Simulation generation error: %s", exc)
            return {
                "competitorName": competitor_name,
                "scenarioTitle": f"{competitor_name} Defensive Simulation",
                "riskLevel": "HIGH",
                "riskScore": 70,
                "projectedMarketShareImpact": "-3.2% short-term pipeline risk",
                "competitorVulnerability": "Compromised unit economics and elevated churn among support-heavy accounts.",
                "immediateCounterMeasure": "Arm account executives with proactive ROI calculators and lock in 2-year renewal terms with price protection.",
                "midTermMoatStrategy": "Ship differentiated ecosystem integrations that their architecture cannot support.",
                "salesRepPlaybook": f"\"We're seeing {competitor_name} cut prices as a concession because their product lacks native integration and enterprise reliability.\"",
                "timelineForecast": [
                    {"phase": "Month 1", "marketImpact": -1.2, "status": "Initial pricing pressure"},
                    {"phase": "Month 2", "marketImpact": -2.5, "status": "Competitor marketing push"},
                    {"phase": "Month 4", "marketImpact": -0.5, "status": "Stabilization phase"},
                    {"phase": "Month 6", "marketImpact": 1.5, "status": "Counter-strategy payoff"}
                ]
            }
