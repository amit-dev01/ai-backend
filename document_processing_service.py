"""
DocumentProcessingService for Phase 2 Live Competitor Monitoring.

Processes scraped raw articles/pages through a 7-step intelligence pipeline:
  1. Check for duplicate document within 24h
  2. Generate concise factual summary via Groq AI
  3. Classify event type via Groq AI
  4. Analyze sentiment via Groq AI
  5. Score specific relevance and reason via Groq AI
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
    "PRICING_CHANGE": 80,
    "PARTNERSHIP": 75,
    "EXPANSION": 70,
    "TECHNOLOGY": 65,
    "LAYOFF": 60,
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


async def _call_groq_with_retry(prompt: str, json_mode: bool = False, model: str = EXTRACTION_MODEL) -> Any:
    """Call Groq API, retrying once after 2s delay on error."""
    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"} if (json_mode and attempt == 0) else None,
                temperature=0.2,
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
    sentiment: str
) -> tuple[int, str]:
    """Calculate deterministic impact score and label based on weights formula."""
    event_weight = EVENT_TYPE_WEIGHTS.get(event_type.upper(), 20)
    comp_weight = (competitive_score / 100.0) if (competitive_score is not None and competitive_score > 0) else 0.5

    sent_upper = (sentiment or "NEUTRAL").upper()
    if sent_upper == "POSITIVE":
        sentiment_weight = 0.8
    elif sent_upper == "NEGATIVE":
        sentiment_weight = 1.0
    else:
        sentiment_weight = 0.5

    raw_impact = (
        event_weight * 0.35
        + comp_weight * 100.0 * 0.25
        + relevance_score * 0.25
        + sentiment_weight * 100.0 * 0.15
    )

    impact_score = max(0, min(100, int(round(raw_impact))))

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
    """Service handling multi-step processing and analysis for a single scraped document."""

    @staticmethod
    async def process_document(
        competitor_id: str,
        company_id: str,
        url: str,
        title: str,
        raw_content: str,
        published_date: Optional[str] = None
    ) -> Optional[dict]:
        """Process raw scraped content into a fully structured intelligence document."""
        # ---------------------------------------------------------------------
        # STEP 1 — Check for duplicate
        # ---------------------------------------------------------------------
        existing_doc = get_document_by_url(url, within_hours=24)
        if existing_doc:
            logger.info("Document already processed within 24h for URL: %s. Skipping.", url)
            return None

        # Fetch company profile and competitor details for context
        company = get_company_profile_by_id(company_id) or {}
        competitor = get_competitor_by_id(competitor_id) or {}

        company_name = company.get("company_name", "Our Company")
        industry = company.get("industry", "Market Segment")
        description = company.get("description", "")
        products_raw = company.get("products_or_services", [])
        products_str = ", ".join(products_raw) if isinstance(products_raw, list) else str(products_raw)
        customer_segments = company.get("target_customers", "")
        primary_problem = description

        competitor_name = competitor.get("name", "Competitor")
        competitive_score = competitor.get("competitive_score")

        # ---------------------------------------------------------------------
        # STEP 2 — Generate summary using Groq
        # ---------------------------------------------------------------------
        summary_prompt = f"""Summarize the following content in 2 to 3 sentences. Focus only on the most important business-relevant information. Be factual and concise. Return only the summary text, no labels, no explanation.

Content:
{raw_content[:3000]}"""

        try:
            summary = await _call_groq_with_retry(summary_prompt, json_mode=False, model=EXTRACTION_MODEL)
        except Exception as exc:
            logger.warning("Summary generation failed for URL %s: %s", url, str(exc))
            summary = (title or "Competitor update") + ": Content extracted from web."

        # ---------------------------------------------------------------------
        # STEP 3 — Classify event type using Groq
        # ---------------------------------------------------------------------
        event_prompt = f"""You are a competitive intelligence analyst. Read the following content about a company and classify it into exactly one event type. Return only valid JSON, no explanation, no markdown.

Content:
{summary}

Return this JSON:
{{
  "eventType": "one of PRODUCT_LAUNCH or PRICING_CHANGE or FUNDING or PARTNERSHIP or ACQUISITION or HIRING or LAYOFF or EXPANSION or TECHNOLOGY or MARKETING or REGULATORY or CUSTOMER_SENTIMENT or OTHER",
  "confidence": integer 0 to 100
}}

Event type definitions:
PRODUCT_LAUNCH: new product, feature, or service announced or released
PRICING_CHANGE: pricing updated, new plans, discounts, or pricing page changes
FUNDING: investment round, venture capital, seed, series A B C, IPO
PARTNERSHIP: collaboration, integration, joint venture, partner announcement
ACQUISITION: company bought another company or was acquired
HIRING: job postings, team expansion, new executive hires
LAYOFF: job cuts, workforce reduction, team downsizing
EXPANSION: entering new markets, new regions, new offices
TECHNOLOGY: new technology, infrastructure, platform, API announced
MARKETING: campaign, rebrand, new website, award, recognition
REGULATORY: compliance, legal, government, certification
CUSTOMER_SENTIMENT: customer reviews, testimonials, complaints
OTHER: does not fit any of the above"""

        event_type = "OTHER"
        event_confidence = 70
        try:
            event_res = await _call_groq_with_retry(event_prompt, json_mode=True, model=EXTRACTION_MODEL)
            if isinstance(event_res, dict):
                raw_type = str(event_res.get("eventType", "OTHER")).upper()
                if raw_type in EVENT_TYPE_WEIGHTS:
                    event_type = raw_type
                event_confidence = int(event_res.get("confidence", 70))
        except Exception as exc:
            logger.warning("Event classification failed for URL %s: %s", url, str(exc))

        # ---------------------------------------------------------------------
        # STEP 4 — Analyze sentiment using Groq
        # ---------------------------------------------------------------------
        sentiment_prompt = f"""Analyze the sentiment of the following content from a competitive intelligence perspective. Consider what this means for the company being written about. Return only valid JSON, no explanation, no markdown.

Content:
{summary}

Return this JSON:
{{
  "sentiment": "one of POSITIVE or NEGATIVE or NEUTRAL",
  "confidence": integer 0 to 100
}}

POSITIVE means: good news for the company, growth, success, wins
NEGATIVE means: bad news for the company, problems, losses, failures
NEUTRAL means: factual update with no clear positive or negative signal"""

        sentiment = "NEUTRAL"
        sentiment_confidence = 50
        try:
            sent_res = await _call_groq_with_retry(sentiment_prompt, json_mode=True, model=EXTRACTION_MODEL)
            if isinstance(sent_res, dict):
                raw_sent = str(sent_res.get("sentiment", "NEUTRAL")).upper()
                if raw_sent in ("POSITIVE", "NEGATIVE", "NEUTRAL"):
                    sentiment = raw_sent
                sentiment_confidence = int(sent_res.get("confidence", 50))
        except Exception as exc:
            logger.warning("Sentiment analysis failed for URL %s: %s", url, str(exc))

        # ---------------------------------------------------------------------
        # STEP 5 — Score relevance using Groq
        # ---------------------------------------------------------------------
        relevance_prompt = f"""You are a competitive intelligence analyst. Assess how relevant this competitor event is to our company specifically. Return only valid JSON, no explanation, no markdown.

OUR COMPANY:
Name: {company_name}
Industry: {industry}
Description: {description}
Products: {products_str}
Target Customers: {customer_segments}
Problem Solved: {primary_problem}

COMPETITOR EVENT:
Competitor: {competitor_name}
Event Type: {event_type}
Summary: {summary}

Return this JSON:
{{
  "relevanceScore": integer 0 to 100,
  "reason": "string of 1 to 2 sentences explaining why this is or is not relevant to our company specifically"
}}

Scoring guide:
90 to 100: directly threatens or affects our core product or customers
70 to 89: significantly relevant to our market or strategy
50 to 69: moderately relevant, worth monitoring
30 to 49: loosely relevant, low priority
0 to 29: not relevant to our company"""

        relevance_score = 50
        relevance_reason = f"Event involving competitor {competitor_name} in {industry} market."
        try:
            rel_res = await _call_groq_with_retry(relevance_prompt, json_mode=True, model=EXTRACTION_MODEL)
            if isinstance(rel_res, dict):
                relevance_score = int(rel_res.get("relevanceScore", 50))
                relevance_reason = rel_res.get("reason", relevance_reason)
        except Exception as exc:
            logger.warning("Relevance scoring failed for URL %s: %s", url, str(exc))

        # ---------------------------------------------------------------------
        # STEP 6 — Calculate impact score using formula
        # ---------------------------------------------------------------------
        impact_score, impact_label = calculate_impact_score(
            event_type=event_type,
            competitive_score=competitive_score,
            relevance_score=relevance_score,
            sentiment=sentiment,
        )

        # ---------------------------------------------------------------------
        # STEP 7 — Save document to database
        # ---------------------------------------------------------------------
        doc_payload = {
            "competitor_id": competitor_id,
            "company_id": company_id,
            "source_url": url,
            "title": title or f"{competitor_name} Update",
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
            logger.info("Successfully processed and saved document ID %s for competitor '%s' (Impact: %d - %s)",
                        saved_doc.get("id"), competitor_name, impact_score, impact_label)
            return saved_doc

        logger.warning("Failed to save processed document to DB for URL: %s", url)
        return doc_payload
