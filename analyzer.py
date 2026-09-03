"""
Analyzer module for Competitor Analysis AI.

Contains two async functions:
  - analyze_competitor: produces a deep structured competitive intelligence
    analysis from extracted signals using the primary LLM (Groq 70b).
  - format_report: converts the analysis JSON into a polished boardroom-ready
    Markdown report using the same 70b model for highest quality output.
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
    """Run deep LLM-powered competitive analysis on extracted competitor signals.

    Uses the primary LLM model (llama-3.3-70b-versatile) with the
    SYSTEM_PROMPT persona and ANALYSIS_PROMPT template to produce a full
    strategic analysis: executive summary, SWOT, Porter's Five Forces,
    win/loss scenarios, next steps, and differentiation strategy.

    Args:
        extracted: Structured data from the extraction step.
        request_data: The original CompetitorRequest as a dict.

    Returns:
        A dictionary containing the complete structured analysis.
    """
    company_name = request_data.get("company_name", "Unknown")
    logger.info("Starting deep competitive analysis for %s", company_name)

    user_prompt = ANALYSIS_PROMPT.format(
        our_company_context=request_data.get(
            "our_company_context",
            "We are a direct competitor in the same market segment.",
        ),
        industry=request_data.get("industry", "Unknown"),
        company_name=company_name,
        focus_areas=", ".join(request_data.get("focus_areas", [])) or "pricing, product, positioning, go-to-market",
        today=date.today().isoformat(),
        extracted_data=json.dumps(extracted, indent=2),
    )

    # Use the large 70b model for analysis — quality matters here
    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            raw_output = response.choices[0].message.content
            analysis = json.loads(raw_output)
            logger.info("Deep competitive analysis complete for %s", company_name)
            return analysis
        except Exception as exc:
            logger.warning("Analysis attempt %d failed for %s: %s", attempt + 1, company_name, str(exc))
            if attempt == 1:
                raise exc

    return {}


async def format_report(analysis: dict, company_name: str) -> str:
    """Convert a structured analysis JSON into a polished boardroom-ready Markdown report.

    Uses the large 70b model to ensure the highest quality prose output
    with all 13 sections including tables, callouts, and tagline recommendation.

    Args:
        analysis: The structured analysis dictionary from analyze_competitor().
        company_name: Name of the competitor, used in the report title.

    Returns:
        A Markdown-formatted string containing the full competitive intelligence report.
    """
    logger.info("Formatting boardroom-ready Markdown report for %s", company_name)

    user_prompt = REPORT_FORMAT_PROMPT.format(
        company_name=company_name,
        date=date.today().isoformat(),
        analysis_json=json.dumps(analysis, indent=2),
    )

    # Using LLM_MODEL (70b) for report formatting too — the quality difference
    # in prose generation justifies it over the smaller extraction model
    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.2,
            )
            markdown_report = response.choices[0].message.content
            logger.info("Markdown report formatted for %s", company_name)
            return markdown_report
        except Exception as exc:
            logger.warning("Report format attempt %d failed for %s: %s", attempt + 1, company_name, str(exc))
            if attempt == 1:
                raise exc

    return f"# Competitive Intelligence Report: {company_name}\n\nReport generation failed."
