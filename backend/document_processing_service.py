"""
DocumentProcessingService for Phase 2 Live Competitor Monitoring.

Processes scraped raw articles/pages through a deep intelligence pipeline:
  1. Check for duplicate document within 24h
  2. Generate rich factual summary with named entities and key numbers via Groq
  3. Classify event type with sub-type and confidence reasoning via Groq
  4. Analyze sentiment + business implication via Groq
  5. Score relevance with threat-level assessment via Groq
  6. Calculate impact score deterministically via weighted formula
  7. Persist document record to database
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional

from openai import AsyncOpenAI

from config import GROQ_API_KEY, GROQ_BASE_URL, EXTRACTION_MODEL, LLM_MODEL
from database import (
    get_document_by_url,
    get_company_profile_by_id,
    get_competitor_by_id,
    save_document,
)

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)

EVENT_TYPE_WEIGHTS = {
    "ACQUISITION": 95,
    "FUNDING": 90,
    "PRODUCT_LAUNCH": 85,
    "PRICING_CHANGE": 82,
    "PARTNERSHIP": 75,
    "EXPANSION": 70,
    "TECHNOLOGY": 65,
    "LAYOFF": 62,
    "HIRING": 55,
    "REGULATORY": 50,
    "MARKETING": 40,
    "CUSTOMER_SENTIMENT": 35,
    "OTHER": 20,
}


def _clean_and_parse_json(text: str) -> Any:
    """Clean markdown backticks and parse JSON string."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


async def _call_groq(prompt: str, json_mode: bool = False, model: str = EXTRACTION_MODEL) -> Any:
    """Call Groq API, retrying once after 2s delay on error."""
    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"} if (json_mode and attempt == 0) else None,
                temperature=0.15,
            )
            raw = response.choices[0].message.content or ""
            if json_mode:
                return _clean_and_parse_json(raw)
            return raw.strip()
        except Exception as exc:
            logger.warning("Groq call attempt %d failed: %s", attempt + 1, str(exc))
            if attempt == 0:
                await asyncio.sleep(2.0)
            else:
                raise exc


def calculate_impact_score(
    event_type: str,
    competitive_score: Optional[int],
    relevance_score: int,
    sentiment: str,
    threat_level: str = "MEDIUM",
) -> tuple[int, str]:
    """Calculate deterministic impact score and label using weighted formula.

    Formula weights:
      35% event type importance
      25% competitor competitive score
      25% AI-assessed relevance to our specific company
      15% sentiment (negative news about competitor = higher urgency for us)
    Bonus: +5 for CRITICAL threat level, +3 for HIGH
    """
    event_weight = EVENT_TYPE_WEIGHTS.get(event_type.upper(), 20)
    comp_weight = (competitive_score / 100.0) if (competitive_score is not None and competitive_score > 0) else 0.5

    sent_upper = (sentiment or "NEUTRAL").upper()
    if sent_upper == "POSITIVE":
        sentiment_weight = 0.85   # positive news for them = threat to us
    elif sent_upper == "NEGATIVE":
        sentiment_weight = 1.0    # negative news for them = opportunity for us (still high impact)
    else:
        sentiment_weight = 0.5

    raw_impact = (
        event_weight * 0.35
        + comp_weight * 100.0 * 0.25
        + relevance_score * 0.25
        + sentiment_weight * 100.0 * 0.15
    )

    # Threat level bonus
    threat_bonus = {"CRITICAL": 5, "HIGH": 3, "MEDIUM": 0, "LOW": -3}.get(threat_level.upper(), 0)
    impact_score = max(0, min(100, int(round(raw_impact + threat_bonus))))

    if impact_score >= 80:
        label = "CRITICAL"
    elif impact_score >= 60:
        label = "HIGH"
    elif impact_score >= 40:
        label = "MEDIUM"
    else:
        label = "LOW"

    return impact_score, label


class DocumentProcessingService:
    """Service handling multi-step deep intelligence processing for a single scraped document."""

    @staticmethod
    async def process_document(
        competitor_id: str,
        company_id: str,
        url: str,
        title: str,
        raw_content: str,
        published_date: Optional[str] = None,
    ) -> Optional[dict]:
        """Process raw scraped content into a fully structured intelligence document."""

        # ----------------------------------------------------------------
        # STEP 1 — Duplicate check (24h window)
        # ----------------------------------------------------------------
        existing_doc = get_document_by_url(url, within_hours=24)
        if existing_doc:
            logger.info("Document already processed within 24h for URL: %s. Skipping.", url)
            return None

        # Fetch company and competitor context for grounded analysis
        company = get_company_profile_by_id(company_id) or {}
        competitor = get_competitor_by_id(competitor_id) or {}

        company_name = company.get("company_name", "Our Company")
        industry = company.get("industry", "Market Segment")
        description = company.get("description", "")
        products_raw = company.get("products_or_services", [])
        products_str = ", ".join(products_raw) if isinstance(products_raw, list) else str(products_raw)
        customer_segments = company.get("target_customers", "")

        competitor_name = competitor.get("name", "Competitor")
        competitive_score = competitor.get("competitive_score")
        competitor_type = competitor.get("type", "DIRECT")

        # Use up to 5000 chars — enough for rich context without hitting limits
        content_excerpt = raw_content[:5000]

        # ----------------------------------------------------------------
        # STEP 2 — Rich summary with key facts, numbers, named entities
        # ----------------------------------------------------------------
        summary_prompt = f"""You are a competitive intelligence analyst. Summarize the following content in 3-4 sentences.
Extract the most important business facts: named companies, specific numbers (funding amounts, user counts, price changes, dates), product names, and strategic moves.
Do NOT be vague. Lead with the most important fact. Be specific and factual.
Return ONLY the summary text, no labels, no explanation.

Competitor being written about: {competitor_name}
Content:
{content_excerpt}"""

        try:
            summary = await _call_groq(summary_prompt, json_mode=False, model=EXTRACTION_MODEL)
        except Exception as exc:
            logger.warning("Summary generation failed for URL %s: %s", url, str(exc))
            summary = f"{competitor_name}: {title or 'Competitor activity detected.'}"

        # ----------------------------------------------------------------
        # STEP 3 — Event classification with reasoning
        # ----------------------------------------------------------------
        event_prompt = f"""You are a competitive intelligence analyst. Classify the following content into exactly one event type.
Return only valid JSON, no explanation, no markdown.

Competitor: {competitor_name}
Content summary: {summary}

Return this JSON:
{{
  "eventType": "one of: PRODUCT_LAUNCH | PRICING_CHANGE | FUNDING | PARTNERSHIP | ACQUISITION | HIRING | LAYOFF | EXPANSION | TECHNOLOGY | MARKETING | REGULATORY | CUSTOMER_SENTIMENT | OTHER",
  "confidence": integer 0 to 100,
  "reasoning": "one sentence explaining why you chose this type",
  "subType": "more specific label e.g. 'Series B Funding', 'Freemium Launch', 'Enterprise Pricing Increase', 'CTO Hire', 'EU Expansion' or null"
}}

Event type definitions:
PRODUCT_LAUNCH: new product, feature, or service announced or released
PRICING_CHANGE: pricing updated, new plans, discounts, or pricing page changes
FUNDING: investment round, venture capital, seed, series A/B/C, IPO, acquisition funding
PARTNERSHIP: collaboration, integration, joint venture, partner announcement
ACQUISITION: company bought another company or was acquired
HIRING: job postings, team expansion, new executive hires, headcount growth
LAYOFF: job cuts, workforce reduction, team downsizing, restructuring
EXPANSION: entering new markets, regions, verticals, or new office openings
TECHNOLOGY: new tech infrastructure, platform overhaul, API, developer tools
MARKETING: rebranding, new campaign, award, press coverage, recognition
REGULATORY: compliance certification, legal issue, government contract, audit
CUSTOMER_SENTIMENT: customer reviews, testimonials, NPS, complaints, churn signals
OTHER: does not fit any of the above"""

        event_type = "OTHER"
        event_confidence = 70
        event_reasoning = ""
        event_sub_type = None

        try:
            event_res = await _call_groq(event_prompt, json_mode=True, model=EXTRACTION_MODEL)
            if isinstance(event_res, dict):
                raw_type = str(event_res.get("eventType", "OTHER")).upper()
                if raw_type in EVENT_TYPE_WEIGHTS:
                    event_type = raw_type
                event_confidence = int(event_res.get("confidence", 70))
                event_reasoning = event_res.get("reasoning", "")
                event_sub_type = event_res.get("subType")
        except Exception as exc:
            logger.warning("Event classification failed for URL %s: %s", url, str(exc))

        # ----------------------------------------------------------------
        # STEP 4 — Sentiment + business implication for us
        # ----------------------------------------------------------------
        sentiment_prompt = f"""Analyze the competitive intelligence implications of this content.
Return only valid JSON, no explanation, no markdown.

Our company: {company_name} ({industry})
Competitor: {competitor_name} (type: {competitor_type})
Event: {event_type}
Summary: {summary}

Return this JSON:
{{
  "sentiment": "POSITIVE | NEGATIVE | NEUTRAL",
  "confidence": integer 0 to 100,
  "sentimentReasoning": "one sentence: why this sentiment for the competitor",
  "businessImplication": "one sentence: what this specifically means for OUR company — is this a threat, opportunity, or neutral signal?",
  "urgencySignal": "IMMEDIATE | MONITOR | LOW_PRIORITY"
}}

POSITIVE: good news for the competitor (product launch, funding, growth, award)
NEGATIVE: bad news for the competitor (layoffs, lawsuits, price cuts under pressure, negative reviews)
NEUTRAL: factual update with no clear directional signal"""

        sentiment = "NEUTRAL"
        sentiment_confidence = 50
        business_implication = ""
        urgency_signal = "MONITOR"

        try:
            sent_res = await _call_groq(sentiment_prompt, json_mode=True, model=EXTRACTION_MODEL)
            if isinstance(sent_res, dict):
                raw_sent = str(sent_res.get("sentiment", "NEUTRAL")).upper()
                if raw_sent in ("POSITIVE", "NEGATIVE", "NEUTRAL"):
                    sentiment = raw_sent
                sentiment_confidence = int(sent_res.get("confidence", 50))
                business_implication = sent_res.get("businessImplication", "")
                urgency_signal = sent_res.get("urgencySignal", "MONITOR")
        except Exception as exc:
            logger.warning("Sentiment analysis failed for URL %s: %s", url, str(exc))

        # ----------------------------------------------------------------
        # STEP 5 — Relevance scoring with threat level
        # ----------------------------------------------------------------
        relevance_prompt = f"""You are a competitive intelligence analyst. Assess how relevant and threatening this competitor event is to our specific company.
Return only valid JSON, no explanation, no markdown.

OUR COMPANY:
Name: {company_name}
Industry: {industry}
Description: {description}
Products/Services: {products_str}
Target Customers: {customer_segments}

COMPETITOR EVENT:
Competitor: {competitor_name} (Competitive Score: {competitive_score}/100, Type: {competitor_type})
Event Type: {event_type}
Sub-type: {event_sub_type or 'N/A'}
Summary: {summary}
Business Implication: {business_implication}

Return this JSON:
{{
  "relevanceScore": integer 0 to 100,
  "threatLevel": "CRITICAL | HIGH | MEDIUM | LOW",
  "reason": "2 sentences: why this is or isn't relevant to us specifically — reference our products and customers",
  "recommendedAction": "one specific verb+object action our team should consider, or 'Monitor' if low priority"
}}

Relevance scoring:
90-100: directly threatens our core product, customers, or revenue
70-89: significantly relevant — same market segment, overlapping customers
50-69: moderately relevant — adjacent market or feature overlap
30-49: loosely relevant — same industry, different segment
0-29: not relevant to our specific business"""

        relevance_score = 50
        threat_level = "MEDIUM"
        relevance_reason = f"Competitor {competitor_name} activity in {industry} market."
        recommended_action = "Monitor"

        try:
            rel_res = await _call_groq(relevance_prompt, json_mode=True, model=EXTRACTION_MODEL)
            if isinstance(rel_res, dict):
                relevance_score = int(rel_res.get("relevanceScore", 50))
                threat_level = str(rel_res.get("threatLevel", "MEDIUM")).upper()
                relevance_reason = rel_res.get("reason", relevance_reason)
                recommended_action = rel_res.get("recommendedAction", "Monitor")
        except Exception as exc:
            logger.warning("Relevance scoring failed for URL %s: %s", url, str(exc))

        # ----------------------------------------------------------------
        # STEP 6 — Impact score calculation
        # ----------------------------------------------------------------
        impact_score, impact_label = calculate_impact_score(
            event_type=event_type,
            competitive_score=competitive_score,
            relevance_score=relevance_score,
            sentiment=sentiment,
            threat_level=threat_level,
        )

        # ----------------------------------------------------------------
        # STEP 7 — Save to database
        # ----------------------------------------------------------------
        doc_payload = {
            "competitor_id": competitor_id,
            "company_id": company_id,
            "source_url": url,
            "title": title or f"{competitor_name} — {event_type.replace('_', ' ').title()}",
            "published_date": published_date,
            "raw_content": raw_content,
            "summary": summary,
            "event_type": event_type,
            "sentiment": sentiment,
            "sentiment_confidence": sentiment_confidence,
            "relevance_score": relevance_score,
            "relevance_reason": relevance_reason,
            "impact_score": impact_score,
            "impact_label": impact_label,
            "is_processed": True,
        }

        saved_doc = save_document(doc_payload)
        if saved_doc:
            logger.info(
                "Processed document for '%s': %s / %s — Impact %d (%s) | Threat: %s | Action: %s",
                competitor_name,
                event_type,
                event_sub_type or "—",
                impact_score,
                threat_level,
                recommended_action,
            )

            # Trigger instant alert for CRITICAL events or structural market moves
            if impact_score >= 80 or event_type in ("PRICING_CHANGE", "ACQUISITION"):
                try:
                    from alert_service import AlertService
                    asyncio.create_task(
                        AlertService.dispatch_critical_event_alert(
                            competitor_name=competitor_name,
                            event_type=event_type,
                            impact_score=impact_score,
                            impact_label=impact_label,
                            title=title or f"{competitor_name} — {event_type.replace('_', ' ').title()}",
                            summary=summary,
                            source_url=url,
                            recommended_action=recommended_action,
                        )
                    )
                except Exception as alert_exc:
                    logger.warning("Alert dispatch hook error: %s", alert_exc)

            return saved_doc

        logger.warning("Failed to save processed document to DB for URL: %s", url)
        return doc_payload
