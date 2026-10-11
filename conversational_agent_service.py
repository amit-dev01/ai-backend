"""
Conversational Intelligence Agent Service.
Powers the interactive "Ask anything about your competitors" assistant.
Retrieves real-time context:
  - Company profile & ICP
  - Tracked competitors & threat scores
  - Pricing matrix insights
  - Recent intelligence documents & market moves
Calls Groq LLM to deliver structured executive answers and follow-up prompts.
"""

import json
import logging
from typing import Any, Optional
from openai import AsyncOpenAI

from config import GROQ_API_KEY, GROQ_BASE_URL, LLM_MODEL
from database import (
    get_company_profile_by_id,
    get_competitors_for_company,
    get_recent_intelligence_documents,
)

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)


class ConversationalAgentService:
    """Provides conversational competitive analysis backed by live database context."""

    @staticmethod
    async def chat(
        company_id: str,
        message: str,
        history: list[dict[str, Any]] = [],
        competitor_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Executes a context-augmented chat turn using Groq LLM.
        """
        company = get_company_profile_by_id(company_id) or {}
        company_name = company.get("company_name", "Our Business")
        industry = company.get("industry", "Technology")
        description = company.get("description", "")
        target_customers = company.get("target_customers", "B2B Customers")

        competitors = get_competitors_for_company(company_id) or []
        accepted_competitors = [c for c in competitors if c.get("is_accepted")] or competitors[:5]
        
        # Build competitor summaries
        comp_summaries = []
        referenced_names = []
        for c in accepted_competitors:
            c_name = c.get("name", "Rival")
            referenced_names.append(c_name)
            score = c.get("competitive_score", 50)
            notes = c.get("description") or c.get("executive_summary") or ""
            comp_summaries.append(f"- {c_name} (Threat Score: {score}/100): {notes[:180]}")

        # Fetch recent intelligence events
        recent_docs = get_recent_intelligence_documents(company_id, limit=6) or []
        events_context = []
        for d in recent_docs:
            c_label = d.get("competitor_name") or "Competitor"
            e_title = d.get("title", "")
            e_type = d.get("event_type", "MARKET_EVENT")
            events_context.append(f"- [{c_label}] {e_type}: {e_title}")

        # Fetch category pricing benchmarks
        pricing_context = ""
        try:
            from pricing_matrix_service import PricingMatrixService
            pm = PricingMatrixService.get_category_pricing_matrix(company_id)
            stats = pm.get("categoryStats", {})
            floor = stats.get("priceFloorMinima", 0)
            ceiling = stats.get("enterpriseCeilingMaxima", 0)
            median = stats.get("categoryMedianPrice", 0)
            whitespace = pm.get("whitespaceGaps", [])
            gap_desc = whitespace[0].get("description", "") if whitespace else "Mid-market gap"
            pricing_context = f"- Price Floor: ${floor}/mo | Category Median: ${median}/mo | Enterprise Ceiling: ${ceiling}/mo\n- Whitespace Monetization: {gap_desc}"
        except Exception:
            pricing_context = "- Category baseline tiers actively tracked."

        # Focus competitor if provided
        focus_comp_text = ""
        if competitor_id:
            for c in accepted_competitors:
                if str(c.get("id")) == str(competitor_id):
                    focus_comp_text = f"\nUSER IS SPECIFICALLY ASKING ABOUT: {c.get('name')}\n"
                    break

        system_prompt = f"""You are Aetheris AI, the executive-grade Competitive Intelligence Advisor for {company_name}.
Your industry: {industry}.
Target ICP: {target_customers}.
Company Overview: {description}

CURRENT COMPETITIVE LANDSCAPE:
{chr(10).join(comp_summaries) if comp_summaries else "No active competitors tracked yet."}

CATEGORY PRICING MATRIX BENCHMARKS:
{pricing_context}

RECENT INTELLIGENCE MOVES DETECTED:
{chr(10).join(events_context) if events_context else "Monitoring active across live feeds."}
{focus_comp_text}
CORE INSTRUCTIONS:
1. Speak as a top-tier competitive intelligence partner (sharp, highly informed, direct). NEVER give vague AI generic advice or generic marketing platitudes.
2. Directly reference specific competitors by name (e.g., {referenced_names[:3] if referenced_names else 'tracked rivals'}) and quote their actual threat scores.
3. Structure your response into two clear executive sections:
   ### 1. Strategic Breakdown
   (Directly address the user's inquiry with facts about rivals, pricing dynamics, or positioning vulnerabilities).
   ### 2. Tactical Playbook
   (Give 2-3 specific action items: Sales battlecard objection counter, Product moat recommendation, or Pricing lever).
4. Keep the total response between 250 and 380 words so it is complete, impactful, and never cuts off mid-sentence.
5. End with a JSON array of 2-3 natural follow-up questions formatted strictly like:
```json
["Follow-up question 1?", "Follow-up question 2?"]
```
"""

        groq_messages = [{"role": "system", "content": system_prompt}]

        # Include prior conversation history (up to last 6 messages)
        for turn in history[-6:]:
            role = "user" if turn.get("role") == "user" else "assistant"
            content = turn.get("content", "")
            if content:
                groq_messages.append({"role": role, "content": content})

        groq_messages.append({"role": "user", "content": message})

        # Try primary model first, fallback to versatile model if needed
        models_to_try = [
            LLM_MODEL or "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "qwen/qwen3.8-27b"
        ]

        raw_reply = ""
        last_error = None

        for model_name in models_to_try:
            try:
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=groq_messages,
                    temperature=0.35,
                    max_tokens=1400,
                )
                raw_reply = response.choices[0].message.content or ""
                if raw_reply.strip():
                    break
            except Exception as exc:
                last_error = exc
                logger.warning("Groq model %s error: %s, attempting fallback...", model_name, exc)
                continue

        if raw_reply:
            # Extract follow-up questions from JSON block if present
            follow_ups = []
            clean_reply = raw_reply
            if "```json" in raw_reply:
                parts = raw_reply.split("```json")
                clean_reply = parts[0].strip()
                json_part = parts[1].split("```")[0].strip()
                try:
                    parsed = json.loads(json_part)
                    if isinstance(parsed, list):
                        follow_ups = [str(q) for q in parsed[:3]]
                except Exception:
                    pass

            if not follow_ups:
                top_rival = referenced_names[0] if referenced_names else "primary competitors"
                follow_ups = [
                    f"How does our pricing directly compare to {top_rival}?",
                    f"What customer objections should sales counter against {top_rival}?",
                    "What category whitespace monetization opportunities exist right now?"
                ]

            return {
                "reply": clean_reply,
                "suggestedFollowUps": follow_ups,
                "referencedCompetitors": referenced_names[:4]
            }

        # Intelligent Context-Grounded Fallback (if external LLM API is unavailable)
        logger.error("All Groq models failed. Generating grounded synthesizer fallback: %s", last_error)
        top_rival = referenced_names[0] if referenced_names else "Primary Competitor"
        second_rival = referenced_names[1] if len(referenced_names) > 1 else "Market Rivals"

        fallback_reply = (
            f"### 1. Strategic Breakdown: {company_name} Competitive Position\n\n"
            f"Based on real-time surveillance across your competitive landscape, primary pressure is concentrated on **{top_rival}** "
            f"and **{second_rival}** for **{target_customers}**.\n\n"
            f"* **Market Pressure:** Competitors are targeting your ICP with aggressive feature announcements and overlapping value claims.\n"
            f"* **Pricing & Value:** Review your Category Pricing Matrix against active competitors. Incumbents currently command enterprise premiums while leaving accessible whitespace gaps.\n\n"
            f"### 2. Tactical Playbook: Immediate Counter-Measures\n\n"
            f"* **Sales Defense:** Equip account reps with battlecard landmines against {top_rival}. Emphasize proprietary specialization, faster deployment, and direct ROI over legacy complexity.\n"
            f"* **Product Moat:** Fortify feature differentiation around enterprise security, dedicated onboarding, and workflow speed to make switching friction high for your core accounts.\n"
            f"* **Pricing Leverage:** Leverage transparent tiering to undercut inflated enterprise quotes from {second_rival} while capturing mid-market demand."
        )

        return {
            "reply": fallback_reply,
            "suggestedFollowUps": [
                f"How does our feature set compare directly to {top_rival}?",
                f"What pricing counter-strategy should we use against {second_rival}?",
                "Which competitor presents the highest immediate churn risk?"
            ],
            "referencedCompetitors": referenced_names[:4]
        }
