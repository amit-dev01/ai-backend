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
from competitor_monitoring_service import _is_recently_scraped
from task_generation_service import TaskGenerationService

logger = logging.getLogger(__name__)

async def run_manual_monitoring_job(company_id: str, job_id: str):
    """
    Executes the 6-step manual monitoring job.
    1. Loading competitors (10%)
    2. Searching for latest competitor activity (20%)
    3. Scraping and processing documents (40%)
    4. Updating trends and anomalies (65%)
    5. Generating updated intelligence summary (85%)
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
            error=error
        )

    try:
        # STEP 1: Loading competitors
        update_status(10, "Loading competitors")
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

        # STEP 2: Searching for latest competitor activity
        update_status(20, "Searching for latest competitor activity")
        all_selected_items = []
        for competitor in competitors:
            comp_name = competitor.get("name", "").strip()
            if not comp_name:
                continue

            try:
                search1 = await search_service.searchCompetitorNews(comp_name)
                search2 = await search_service.searchCompetitorActivity(comp_name, "product launch")
                search3 = await search_service.searchCompetitorActivity(comp_name, "funding")

                all_search_items = search1 + search2 + search3
                documents_found += len(all_search_items)

                seen_urls = set()
                unique_items = []
                for item in all_search_items:
                    url = item.get("url", "").strip()
                    if url and url not in seen_urls and search_service._is_allowed_url(url):
                        seen_urls.add(url)
                        unique_items.append(item)

                # Filter out recently scraped
                new_items = [item for item in unique_items if not _is_recently_scraped(item["url"], days=7)]
                
                # Assign competitor context to the item for the next step
                for item in new_items[:5]:  # Capped at 5 per competitor
                    item["_comp_id"] = competitor.get("id")
                    all_selected_items.append(item)
            except Exception as e:
                logger.warning(f"Failed to search activity for {comp_name}: {e}")

        update_status(20, "Searching for latest competitor activity") # Update doc counts

        # STEP 3: Scraping and processing documents
        update_status(40, "Scraping and processing documents")
        for idx, item in enumerate(all_selected_items):
            url = item["url"]
            title = item.get("title", "")
            published_date = item.get("publishedDate")
            comp_id = item["_comp_id"]

            try:
                content = await scrape_website(url)
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
                        
                        # Trigger task generation asynchronously
                        impact = processed_doc.get("impact_label")
                        if impact in ("CRITICAL", "HIGH") and processed_doc.get("id"):
                            asyncio.create_task(TaskGenerationService.generateTaskFromDocument(
                                str(processed_doc["id"]), company_id
                            ))
                            
                        # Update status every time a doc is processed so progress is visible
                        update_status(40, "Scraping and processing documents")
            except Exception as e:
                logger.warning(f"Failed scraping or processing URL {url}: {e}")
            
            if idx < len(all_selected_items) - 1:
                await asyncio.sleep(1.0)

        # STEP 4: Updating trends and anomalies
        update_status(65, "Updating trends and anomalies")
        # Services for trend and anomaly detection are not yet implemented.
        # Placeholders for future task generation integration:
        # new_trends = await TrendDetectionService.run(company_id)
        # for trend in (new_trends or []):
        #     if trend.get("severity") in ("CRITICAL", "HIGH") and trend.get("id"):
        #         asyncio.create_task(TaskGenerationService.generateTaskFromTrend(trend["id"], company_id))
        # 
        # new_anomalies = await AnomalyDetectionService.run(company_id)
        # for anomaly in (new_anomalies or []):
        #     if anomaly.get("severity") in ("CRITICAL", "HIGH") and anomaly.get("id"):
        #         asyncio.create_task(TaskGenerationService.generateTaskFromAnomaly(anomaly["id"], company_id))
        await asyncio.sleep(0.5)

        # STEP 5: Generating updated intelligence summary
        update_status(85, "Generating updated intelligence summary")
        try:
            await IntelligenceSummaryService.generateWeeklySummary(company_id)
        except Exception as e:
            logger.warning(f"Failed to generate intelligence summary: {e}")

        # STEP 6: Completed
        update_status(100, "Completed", status="COMPLETED")

    except Exception as exc:
        logger.exception(f"Manual Monitoring Job failed for company {company_id}: {exc}")
        update_status(0, "Check failed", status="FAILED", error=str(exc))
