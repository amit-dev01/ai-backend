"""
Scheduler module for Phase 2 Live Competitor Monitoring.

Manages scheduled background cron jobs:
  - Daily News Monitoring (default 08:00 daily)
  - Weekly Page Monitoring (default 09:00 Mondays)
  - Weekly Intelligence Summary (default 10:00 Mondays)
"""

import asyncio
import logging
from typing import Optional

from config import MONITORING_SCHEDULE_NEWS, MONITORING_SCHEDULE_PAGES
from database import get_completed_companies
from competitor_monitoring_service import CompetitorMonitoringService
from intelligence_summary_service import IntelligenceSummaryService

logger = logging.getLogger(__name__)

_scheduler = None


async def run_daily_news_monitoring_job():
    """Run daily news monitoring sequentially across all completed companies."""
    logger.info("=== Running Scheduled Job: Daily News Monitoring ===")
    companies = get_completed_companies()
    for idx, company in enumerate(companies):
        company_id = str(company.get("id", ""))
        if company_id:
            try:
                await CompetitorMonitoringService.runNewsMonitoring(company_id)
            except Exception as exc:
                logger.exception("Error during daily news job for company %s: %s", company_id, str(exc))

        if idx < len(companies) - 1:
            await asyncio.sleep(5.0)


async def run_weekly_page_monitoring_job():
    """Run weekly website page change monitoring sequentially across all completed companies."""
    logger.info("=== Running Scheduled Job: Weekly Page Monitoring ===")
    companies = get_completed_companies()
    for idx, company in enumerate(companies):
        company_id = str(company.get("id", ""))
        if company_id:
            try:
                await CompetitorMonitoringService.runPageMonitoring(company_id)
            except Exception as exc:
                logger.exception("Error during weekly page job for company %s: %s", company_id, str(exc))

        if idx < len(companies) - 1:
            await asyncio.sleep(5.0)


async def run_weekly_summary_job():
    """Run weekly strategic summary generation sequentially across all completed companies."""
    logger.info("=== Running Scheduled Job: Weekly AI Intelligence Summary ===")
    companies = get_completed_companies()
    for idx, company in enumerate(companies):
        company_id = str(company.get("id", ""))
        if company_id:
            try:
                await IntelligenceSummaryService.generateWeeklySummary(company_id)
            except Exception as exc:
                logger.exception("Error during weekly summary job for company %s: %s", company_id, str(exc))

        if idx < len(companies) - 1:
            await asyncio.sleep(5.0)


def start_scheduler():
    """Initialize and start background cron scheduler."""
    global _scheduler
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        _scheduler = AsyncIOScheduler()

        # Parse cron expressions
        news_parts = MONITORING_SCHEDULE_NEWS.split()
        page_parts = MONITORING_SCHEDULE_PAGES.split()

        if len(news_parts) == 5:
            news_trigger = CronTrigger(
                minute=news_parts[0],
                hour=news_parts[1],
                day=news_parts[2],
                month=news_parts[3],
                day_of_week=news_parts[4],
            )
        else:
            news_trigger = CronTrigger(hour=8, minute=0)

        if len(page_parts) == 5:
            page_trigger = CronTrigger(
                minute=page_parts[0],
                hour=page_parts[1],
                day=page_parts[2],
                month=page_parts[3],
                day_of_week=page_parts[4],
            )
        else:
            page_trigger = CronTrigger(day_of_week="mon", hour=9, minute=0)

        summary_trigger = CronTrigger(day_of_week="mon", hour=10, minute=0)

        _scheduler.add_job(run_daily_news_monitoring_job, news_trigger, id="daily_news_monitoring")
        _scheduler.add_job(run_weekly_page_monitoring_job, page_trigger, id="weekly_page_monitoring")
        _scheduler.add_job(run_weekly_summary_job, summary_trigger, id="weekly_summary_generation")

        _scheduler.start()
        logger.info("APScheduler initialized successfully with daily and weekly monitoring jobs.")
    except ImportError:
        logger.warning("APScheduler module not installed. Scheduled cron jobs disabled (manual trigger available).")
    except Exception as exc:
        logger.warning("Failed to start APScheduler: %s", str(exc))


def stop_scheduler():
    """Stop background scheduler."""
    global _scheduler
    if _scheduler:
        try:
            _scheduler.shutdown()
            logger.info("APScheduler shut down successfully.")
        except Exception:
            pass
