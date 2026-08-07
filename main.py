"""
Main FastAPI application for Competitor Analysis AI.

Exposes two endpoints:
  - GET  /          → Health check
  - POST /analyze   → Full competitor analysis pipeline

The /analyze endpoint orchestrates: scraping → extraction → analysis →
report formatting → file save → JSON response.
"""

import logging
import re
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from models import CompetitorRequest, CompetitorReport
from scraper import scrape_website, scrape_social
from extractor import extract_signals
from analyzer import analyze_competitor, format_report
from database import save_competitor_and_report

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Competitor Analysis AI",
    version="1.0",
    description=(
        "AI-powered competitive intelligence API. Submit a competitor's name "
        "and website to receive a full business-grade analysis report."
    ),
)

# CORS — allow frontend on different port during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Startup: ensure reports directory exists
# ---------------------------------------------------------------------------
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def _slugify(text: str) -> str:
    """Convert a string to a filesystem-safe slug.

    Args:
        text: The string to slugify.

    Returns:
        A lowercase, hyphen-separated slug safe for filenames.
    """
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
async def health_check() -> dict:
    """Health-check endpoint returning service status."""
    return {"status": "ok", "service": "competitor-analysis-ai"}


@app.post("/analyze", response_model=CompetitorReport)
async def analyze(req: CompetitorRequest) -> CompetitorReport:
    """Run the full competitor analysis pipeline.

    Steps:
        1. Scrape the competitor's website using Crawl4AI.
        2. Best-effort scrape any provided social URLs.
        3. Extract structured signals from scraped content via LLM.
        4. Perform deep competitive analysis via LLM.
        5. Format analysis as a polished Markdown report.
        6. Save the report to disk.
        7. Return a CompetitorReport JSON response.

    Args:
        req: A CompetitorRequest with company_name, website_url, etc.

    Returns:
        CompetitorReport containing structured analysis + full Markdown report.

    Raises:
        HTTPException: 500 if any step in the pipeline fails.
    """
    try:
        # --- 1. Scrape website ------------------------------------------------
        logger.info("=== Pipeline start: %s (%s) ===", req.company_name, req.website_url)
        website_content = await scrape_website(str(req.website_url))

        # --- 2. Scrape social URLs (best-effort) -----------------------------
        social_parts: list[str] = []
        for platform, social_url in req.social_urls.items():
            logger.info("Scraping social: %s → %s", platform, social_url)
            social_content = await scrape_social(social_url)
            if social_content:
                social_parts.append(f"\n\n[{platform.upper()}]\n{social_content}")

        # --- 3. Combine all content ------------------------------------------
        full_content = website_content + "".join(social_parts)
        logger.info("Total scraped content: %d characters", len(full_content))

        # --- 4. Extract signals -----------------------------------------------
        extracted = await extract_signals(full_content, req.company_name)
        logger.info("Extraction complete — keys: %s", list(extracted.keys()))

        # --- 5. Analyze -------------------------------------------------------
        request_data = req.model_dump()
        # Convert HttpUrl to plain string for serialisation
        request_data["website_url"] = str(request_data["website_url"])
        analysis = await analyze_competitor(extracted, request_data)
        logger.info("Analysis complete for %s", req.company_name)

        # --- 6. Format Markdown report ----------------------------------------
        markdown_report = await format_report(analysis, req.company_name)

        # --- 7. Save report to disk -------------------------------------------
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        slug = _slugify(req.company_name)
        report_filename = f"{slug}_{timestamp}.md"
        report_path = REPORTS_DIR / report_filename
        report_path.write_text(markdown_report, encoding="utf-8")
        logger.info("Report saved to disk: %s", report_path)

        # --- 8. Save report & competitor to Supabase --------------------------
        db_saved = await save_competitor_and_report(
            req_data=request_data,
            extracted=extracted,
            analysis=analysis,
            markdown_report=markdown_report,
        )
        if db_saved:
            logger.info("Saved to Supabase: competitor_id=%s, report_id=%s", db_saved.get("competitor_id"), db_saved.get("report_id"))

        # --- 9. Build response ------------------------------------------------
        report = CompetitorReport(
            company_name=req.company_name,
            executive_summary=analysis.get("executive_summary", ""),
            snapshot=analysis.get("competitor_snapshot", {}),
            strengths=analysis.get("strengths", []),
            weaknesses=analysis.get("weaknesses", []),
            opportunities=analysis.get("opportunities_for_us", []),
            threats=analysis.get("threats_to_us", []),
            swot=analysis.get("swot", {}),
            next_steps=analysis.get("next_steps", []),
            differentiation_strategy=analysis.get("differentiation_strategy", ""),
            full_markdown_report=markdown_report,
            generated_at=datetime.utcnow(),
        )

        logger.info("=== Pipeline complete: %s ===", req.company_name)
        return report

    except Exception as exc:
        logger.exception("Pipeline failed for %s: %s", req.company_name, str(exc))
        raise HTTPException(
            status_code=500,
            detail=f"Analysis pipeline failed: {str(exc)}",
        ) from exc


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
