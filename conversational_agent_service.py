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

        # Focus competitor if provided
        focus_comp_text = ""
        if competitor_id:
            for c in accepted_competitors:
                if str(c.get("id")) == str(competitor_id):
                    focus_comp_text = f"\nUSER IS SPECIFICALLY ASKING ABOUT: {c.get('name')}\n"
                    break

        system_prompt = f"""You are Aetheris AI, the premier Competitive Intelligence Co-Pilot for {company_name}.
Your industry: {industry}.
Our ICP / Market: {target_customers}.
Our Overview: {description}

CURRENT COMPETITIVE LANDSCAPE:
{chr(10).join(comp_summaries) if comp_summaries else "No active competitors tracked yet."}

RECENT INTELLIGENCE MOVES DETECTED:
{chr(10).join(events_context) if events_context else "No recent market events recorded."}
{focus_comp_text}
CORE OBJECTIVES:
1. Provide razor-sharp, executive-grade answers about competitor pricing, vulnerabilities, feature roadmaps, and defensive strategies.
2. Directly answer "So what should we do about it?" by including concrete tactical recommendations (Sales tactics, Product moats, Pricing leverage).
3. Keep answers crisp and formatted with clear markdown bullet points. Avoid generic fluff.
4. Conclude with 2-3 brief follow-up question ideas the user can ask next. Format follow-ups at the very end in a JSON block:
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

        try:
            response = await client.chat.completions.create(
                model=LLM_MODEL or "qwen/qwen3.8-27b",
                messages=groq_messages,
                temperature=0.3,
                max_tokens=800,
            )
            raw_reply = response.choices[0].message.content or ""
            
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
                follow_ups = [
                    f"How does our pricing compare against {referenced_names[0] if referenced_names else 'competitors'}?",
                    "What are their biggest customer complaints?",
                    "What counter-playbook should sales use this week?"
                ]

            return {
                "reply": clean_reply,
                "suggestedFollowUps": follow_ups,
                "referencedCompetitors": referenced_names[:4]
            }

        except Exception as exc:
            logger.error("Groq chat completion error: %s", exc)
            return {
                "reply": f"Based on currently monitored signals for {company_name}, competitors are actively competing for {target_customers}. Review your Tactical Battlecards and Pricing Matrix to maintain defensive positioning.",
                "suggestedFollowUps": ["Review pricing matrix", "Check recent threats", "Inspect tactical battlecards"],
                "referencedCompetitors": referenced_names[:4]
            }
