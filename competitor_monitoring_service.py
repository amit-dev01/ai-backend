"""
CompetitorMonitoringService module for Phase 2 Live Competitor Monitoring.

Orchestrates news monitoring and page change monitoring across all accepted competitors of a company.
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional

import search_service
from scraper import scrape_website
from database import (
    get_accepted_competitors_for_company,
    get_url_cache,
    upsert_url_cache,
    create_monitoring_job,
    update_monitoring_job,
)
from document_processing_service import DocumentProcessingService

logger = logging.getLogger(__name__)


def _is_recently_scraped(url: str, days: int = 7) -> bool:
    """Return True if the URL was scraped within the last N days."""
    cached = get_url_cache(url)
    if not cached:
        return False
    scraped_at_str = cached.get("scraped_at")
    if not scraped_at_str:
        return False
    try:
        scraped_at = datetime.fromisoformat(scraped_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
        return (datetime.utcnow() - scraped_at).total_seconds() < (days * 86400)
    except Exception:
        return False


class CompetitorMonitoringService:
    """Orchestrates scheduled news and website page monitoring jobs."""

    @staticmethod
    async def runNewsMonitoring(company_id: str) -> Optional[dict]:
        """Execute news & activity monitoring job for all accepted competitors of a company."""
        logger.info("=== Starting Daily News Monitoring Job for Company ID: %s ===", company_id)

        job = create_monitoring_job(company_id=company_id, competitor_id=None, job_type="NEWS_MONITORING")
        job_id = job.get("id") if job else None

        documents_found = 0
        documents_processed = 0

        try:
            competitors = get_accepted_competitors_for_company(company_id)
            if not competitors:
                logger.info("No accepted competitors found for company %s. Finishing job.", company_id)
                if job_id:
                    update_monitoring_job(job_id, status="COMPLETED", documents_found=0, documents_processed=0)
                return job

            for competitor in competitors:
                comp_id = competitor.get("id")
                comp_name = competitor.get("name", "").strip()
                if not comp_name:
                    continue

                logger.info("Monitoring news for competitor '%s' (ID: %s)...", comp_name, comp_id)

                # Execute 3 searches
                search1 = await search_service.searchCompetitorNews(comp_name)
                search2 = await search_service.searchCompetitorActivity(comp_name, "product launch")
                search3 = await search_service.searchCompetitorActivity(comp_name, "funding")

                all_search_items = search1 + search2 + search3
                documents_found += len(all_search_items)

                # Deduplicate URLs
                seen_urls = set()
                unique_items = []
                for item in all_search_items:
                    url = item.get("url", "").strip()
                    if url and url not in seen_urls and search_service._is_allowed_url(url):
                        seen_urls.add(url)
                        unique_items.append(item)

                # Filter out URLs scraped within last 7 days
                new_items = [item for item in unique_items if not _is_recently_scraped(item["url"], days=7)]

                # Cap maximum 5 new URLs per competitor per run
                selected_items = new_items[:5]
                logger.info("Found %d new URLs (capped at 5) for competitor '%s'", len(selected_items), comp_name)

                for idx, item in enumerate(selected_items):
                    url = item["url"]
                    title = item.get("title", "")
                    published_date = item.get("publishedDate")

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
                        else:
                            logger.warning("Empty Jina scrape content for news URL: %s", url)
                    except Exception as exc:
                        logger.warning("Failed scraping or processing news URL %s: %s", url, str(exc))

                    # 1 second delay between Jina calls
                    if idx < len(selected_items) - 1:
                        await asyncio.sleep(1.0)

            logger.info("=== News Monitoring Job Completed for Company %s (Found: %d, Processed: %d) ===",
                        company_id, documents_found, documents_processed)

            if job_id:
                return update_monitoring_job(
                    job_id,
                    status="COMPLETED",
                    documents_found=documents_found,
                    documents_processed=documents_processed,
                )
            return job

        except Exception as exc:
            logger.exception("Daily News Monitoring Job failed for company %s: %s", company_id, str(exc))
            if job_id:
                update_monitoring_job(
                    job_id,
                    status="FAILED",
                    documents_found=documents_found,
                    documents_processed=documents_processed,
                    error=str(exc),
                )
            return None

    @staticmethod
    async def runPageMonitoring(company_id: str) -> Optional[dict]:
        """Execute weekly website page monitoring job for all accepted competitors of a company."""
        logger.info("=== Starting Weekly Page Monitoring Job for Company ID: %s ===", company_id)

        job = create_monitoring_job(company_id=company_id, competitor_id=None, job_type="PAGE_MONITORING")
        job_id = job.get("id") if job else None

        documents_found = 0
        documents_processed = 0

        try:
            competitors = get_accepted_competitors_for_company(company_id)
            if not competitors:
                logger.info("No accepted competitors found for company %s. Finishing job.", company_id)
                if job_id:
                    update_monitoring_job(job_id, status="COMPLETED", documents_found=0, documents_processed=0)
                return job

            for competitor in competitors:
                comp_id = competitor.get("id")
                comp_name = competitor.get("name", "").strip()
                website = (competitor.get("website_url") or competitor.get("website") or "").strip()

                if not website:
                    continue

                clean_website = website.rstrip("/")
                pages_to_monitor = [
                    clean_website,
                    f"{clean_website}/pricing",
                    f"{clean_website}/blog",
                ]

                documents_found += len(pages_to_monitor)

                for idx, page_url in enumerate(pages_to_monitor):
                    if _is_recently_scraped(page_url, days=7):
                        logger.info("Page %s was recently scraped within 7 days. Skipping.", page_url)
                        continue

                    try:
                        content = await scrape_website(page_url)
                        if content and len(content.strip()) > 50:
                            new_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                            cached = get_url_cache(page_url)
                            old_hash = cached.get("content_hash") if cached else None

                            if old_hash != new_hash:
                                logger.info("Page content changed for %s! Processing document...", page_url)
                                upsert_url_cache(page_url, new_hash)
                                processed_doc = await DocumentProcessingService.process_document(
                                    competitor_id=comp_id,
                                    company_id=company_id,
                                    url=page_url,
                                    title=f"{comp_name} Page Update - {page_url}",
                                    raw_content=content,
                                    published_date=datetime.utcnow().isoformat(),
                                )
                                if processed_doc:
                                    documents_processed += 1
                            else:
                                logger.info("No page content change detected for %s. Updating timestamp only.", page_url)
                                upsert_url_cache(page_url, new_hash)
                        else:
                            logger.warning("Empty content scraped for page %s", page_url)
                    except Exception as exc:
                        logger.warning("Failed page monitoring for %s: %s", page_url, str(exc))

                    # 1 second delay between Jina calls
                    await asyncio.sleep(1.0)

            logger.info("=== Page Monitoring Job Completed for Company %s (Found: %d, Processed: %d) ===",
                        company_id, documents_found, documents_processed)

            if job_id:
                return update_monitoring_job(
                    job_id,
                    status="COMPLETED",
                    documents_found=documents_found,
                    documents_processed=documents_processed,
                )
            return job

        except Exception as exc:
            logger.exception("Weekly Page Monitoring Job failed for company %s: %s", company_id, str(exc))
            if job_id:
                update_monitoring_job(
                    job_id,
                    status="FAILED",
                    documents_found=documents_found,
                    documents_processed=documents_processed,
                    error=str(exc),
                )
            return None
