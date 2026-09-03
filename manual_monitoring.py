"""
Manual monitoring job for Competitor Analysis AI.

Executes a 6-step real-time competitive intelligence check triggered by the user
via the /check-now endpoint. Runs broader searches (5 search types per competitor),
processes every unique URL without time-gate restrictions, and generates an updated
intelligence brief upon completion.
"""

import asyncio
import hashlib
import logging
from typing import Optional

import search_service
from scraper import scrape_website
from database import (
    get_company_profile_by_id,
    get_competitors_for_company,
    upsert_url_cache,
    update_monitoring_job,
)
from document_processing_service import DocumentProcessingService
from intelligence_summary_service import IntelligenceSummaryService
from task_generation_service import TaskGenerationService

logger = logging.getLogger(__name__)


async def run_manual_monitoring_job(company_id: str, job_id: str):
    """
    Execute the 6-step manual competitive intelligence monitoring job.

    Steps:
    1. Load competitors (10%)
    2. Search for latest competitor activity — 5 search types per competitor (25%)
    3. Scrape and process all unique URLs — no time-gate, 24h dedup in processor (75%)
    4. Trend/anomaly detection placeholder (80%)
    5. Generate updated intelligence summary brief (95%)
    6. Completed (100%)
    """
    documents_found = 0
    documents_processed = 0

    def update_status(progress: int, step: str, status: str = "RUNNING", error: Optional[str] = None):
        update_monitoring_job(
            job_id=job_id,
            status=status,
            documents_found=documents_found,
            documents_processed=documents_processed,
            progress=progress,
            current_step=step,
            error=error,
        )

    try:
        # ----------------------------------------------------------------
        # STEP 1 — Load competitors
        # ----------------------------------------------------------------
        update_status(10, "Loading competitors and company context...")
        company = get_company_profile_by_id(company_id)
        if not company:
            update_status(100, "Company not found", status="FAILED", error="Company not found")
            return

        max_comps = company.get("max_competitors_monitored", 10)
        competitors = get_competitors_for_company(company_id, status="active", accepted="true")
        competitors = competitors[:max_comps]

        if not competitors:
            update_status(100, "No active competitors to check", status="COMPLETED")
            return

        total_competitors = len(competitors)
        logger.info("Manual check: processing %d competitors for company %s", total_competitors, company_id)

        # ----------------------------------------------------------------
        # STEP 2 — Broad search across 5 event types per competitor
        # ----------------------------------------------------------------
        update_status(15, f"Searching latest activity for {total_competitors} competitor(s)...")
        all_selected_items = []

        for comp_idx, competitor in enumerate(competitors):
            comp_name = competitor.get("name", "").strip()
            comp_id = competitor.get("id")
            if not comp_name:
                continue

            try:
                # 5 targeted searches cover all major event types
                results = await asyncio.gather(
                    search_service.searchCompetitorNews(comp_name),
                    search_service.searchCompetitorActivity(comp_name, "product launch OR new feature"),
                    search_service.searchCompetitorActivity(comp_name, "funding OR investment"),
                    search_service.searchCompetitorActivity(comp_name, "acquisition OR partnership"),
                    search_service.searchCompetitorActivity(comp_name, "layoffs OR expansion OR pricing"),
                    return_exceptions=True,
                )

                combined = []
                for r in results:
                    if isinstance(r, list):
                        combined.extend(r)

                documents_found += len(combined)

                # Deduplicate URLs within this competitor's results
                seen_urls = set()
                unique_items = []
                for item in combined:
                    url = item.get("url", "").strip()
                    if url and url not in seen_urls and search_service._is_allowed_url(url):
                        seen_urls.add(url)
                        item["_comp_id"] = comp_id
                        unique_items.append(item)

                # Take top 8 per competitor — DocumentProcessingService handles 24h dedup
                for item in unique_items[:8]:
                    all_selected_items.append(item)

            except Exception as e:
                logger.warning("Failed to search activity for %s: %s", comp_name, str(e))

            search_progress = 15 + int(((comp_idx + 1) / total_competitors) * 10)
            update_status(search_progress, f"Searched {comp_idx + 1}/{total_competitors} competitors...")

        logger.info("Manual check: %d total unique URLs to process", len(all_selected_items))

        # ----------------------------------------------------------------
        # STEP 3 — Scrape + process all unique URLs (no time gate)
        # ----------------------------------------------------------------
        total_items = len(all_selected_items)
        if total_items == 0:
            update_status(75, "No new URLs found to process")
        else:
            for idx, item in enumerate(all_selected_items):
                url = item["url"]
                title = item.get("title", "")
                published_date = item.get("publishedDate")
                comp_id = item["_comp_id"]

                doc_progress = 25 + int(((idx + 1) / total_items) * 50)
                update_status(doc_progress, f"Processing document {idx + 1} of {total_items}: {title[:60] or url[:60]}...")

                try:
                    content = await scrape_website(url, bypass_cache=True)
                    if content and len(content.strip()) > 50:
                        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                        upsert_url_cache(url, content_hash)

                        processed_doc = await DocumentProcessingService.process_document(
                            competitor_id=comp_id,
                            company_id=company_id,
                            url=url,
                            title=title,
                            raw_content=content,
                            published_date=published_date,
                        )
                        if processed_doc:
                            documents_processed += 1

                            # Auto-generate action tasks for high-impact events
                            impact = processed_doc.get("impact_label")
                            doc_id = processed_doc.get("id")
                            if impact in ("CRITICAL", "HIGH") and doc_id:
                                asyncio.create_task(
                                    TaskGenerationService.generateTaskFromDocument(str(doc_id), company_id)
                                )
                    else:
                        logger.warning("Empty or too-short content from Jina for URL: %s", url)
                except Exception as e:
                    logger.warning("Failed scraping or processing URL %s: %s", url, str(e))

                if idx < total_items - 1:
                    await asyncio.sleep(0.8)

        # ----------------------------------------------------------------
        # STEP 4 — Trend + anomaly detection (stub — future implementation)
        # ----------------------------------------------------------------
        update_status(80, "Running trend analysis...")
        # Future: TrendDetectionService.run(company_id), AnomalyDetectionService.run(company_id)
        await asyncio.sleep(0.2)

        # ----------------------------------------------------------------
        # STEP 5 — Generate updated intelligence summary brief
        # ----------------------------------------------------------------
        update_status(85, "Generating updated intelligence brief...")
        try:
            await IntelligenceSummaryService.generateWeeklySummary(company_id)
        except Exception as e:
            logger.warning("Failed to generate intelligence summary: %s", str(e))

        # ----------------------------------------------------------------
        # STEP 6 — Complete
        # ----------------------------------------------------------------
        update_status(100, f"Completed — {documents_processed} document(s) processed", status="COMPLETED")
        logger.info(
            "Manual monitoring completed for company %s: found=%d, processed=%d",
            company_id, documents_found, documents_processed,
        )

    except Exception as exc:
        logger.exception("Manual Monitoring Job failed for company %s: %s", company_id, str(exc))
        update_status(0, "Check failed", status="FAILED", error=str(exc))
