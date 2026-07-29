"""
Analyzer module for Competitor Analysis AI.

Contains two async functions:
  - analyze_competitor: produces a structured competitive intelligence analysis
    from extracted signals using the primary LLM model (Groq).
  - format_report: converts the analysis JSON into a polished Markdown report
    using the extraction (smaller/faster) model (Groq).
"""

import json
import logging
from datetime import date

from openai import AsyncOpenAI

from config import GROQ_API_KEY, GROQ_BASE_URL, LLM_MODEL, EXTRACTION_MODEL
from prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT, REPORT_FORMAT_PROMPT

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)


async def analyze_competitor(extracted: dict, request_data: dict) -> dict:
    """Run LLM-powered competitive analysis on extracted competitor signals.

    Uses the primary LLM model (e.g. llama-3.3-70b-versatile) with the
    SYSTEM_PROMPT persona and ANALYSIS_PROMPT template to produce a structured
    analysis including executive summary, SWOT, next steps, and differentiation
    strategy.

    Args:
        extracted: Structured data from the extraction step.
        request_data: The original CompetitorRequest as a dict, providing
            company_name, industry, our_company_context, and focus_areas.

    Returns:
        A dictionary containing the full structured analysis (executive_summary,
        competitor_snapshot, strengths, weaknesses, etc.).
    """
    company_name = request_data.get("company_name", "Unknown")
    logger.info("Starting competitive analysis for %s", company_name)

    user_prompt = ANALYSIS_PROMPT.format(
        our_company_context=request_data.get(
            "our_company_context",
            "We are a similar business competing in the same market.",
        ),
        industry=request_data.get("industry", "Unknown"),
        company_name=company_name,
        focus_areas=", ".join(request_data.get("focus_areas", [])),
        extracted_data=json.dumps(extracted, indent=2),
    )

    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )

    raw_output = response.choices[0].message.content
    analysis = json.loads(raw_output)

    logger.info("Competitive analysis complete for %s", company_name)
    return analysis


async def format_report(analysis: dict, company_name: str) -> str:
    """Convert a structured analysis JSON into a polished Markdown report.

    Uses the extraction model (lighter/faster) to format the analysis into
    an executive-ready Markdown document following a fixed template.

    Args:
        analysis: The structured analysis dictionary from analyze_competitor().
        company_name: Name of the competitor, used in the report title.

    Returns:
        A Markdown-formatted string containing the full competitive intelligence report.
    """
    logger.info("Formatting Markdown report for %s", company_name)

    user_prompt = REPORT_FORMAT_PROMPT.format(
        company_name=company_name,
        date=date.today().isoformat(),
        analysis_json=json.dumps(analysis, indent=2),
    )

    response = await client.chat.completions.create(
        model=EXTRACTION_MODEL,
        messages=[
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    markdown_report = response.choices[0].message.content

    logger.info("Markdown report formatted for %s", company_name)
    return markdown_report
