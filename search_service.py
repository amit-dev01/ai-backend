"""
SearchService for Competitor Discovery Pipeline.

Provides two search provider integrations:
  - Exa AI (semantic search — primary for competitor discovery)
  - Serper (Google search — primary for news, fallback for competitors)

Each public function tries the primary provider first and falls back to
the secondary on any exception, ensuring maximum resilience.
"""

from datetime import datetime, timedelta
import logging
from typing import Optional

import httpx

from config import EXA_API_KEY, SERPER_API_KEY, NEWS_API_KEY

logger = logging.getLogger(__name__)

EXA_BASE_URL = "https://api.exa.ai/search"
SERPER_BASE_URL = "https://google.serper.dev/search"
NEWSAPI_BASE_URL = "https://newsapi.org/v2/everything"

BLOCKED_DOMAINS = {
    "wikipedia.org",
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "youtube.com",
    "reddit.com",
    "tiktok.com",
    "pinterest.com",
    "quora.com",
}


def _is_allowed_url(url: str) -> bool:
    """Return True if the URL is not a blocked social/wiki domain.

    Exception: allow blocked domains if the URL contains keywords like
    'alternatives', 'vs', 'compare' — these are useful comparison pages.
    """
    comparison_keywords = ("alternative", "vs", "compare", "top-", "best-")
    url_lower = url.lower()
    if any(kw in url_lower for kw in comparison_keywords):
        return True
    for domain in BLOCKED_DOMAINS:
        if domain in url_lower:
            return False
    return True


async def _search_exa(query: str, num_results: int = 10) -> list[dict]:
    """Call Exa AI semantic search API and return normalised results."""
    if not EXA_API_KEY:
        raise ValueError("EXA_API_KEY not configured")

    payload = {
        "query": query,
        "numResults": num_results,
        "useAutoprompt": True,
        "contents": {"text": True},
    }
    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(EXA_BASE_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "snippet": (item.get("text") or item.get("snippet") or "")[:500],
                "publishedDate": item.get("publishedDate") or item.get("date"),
            }
        )
    return results


async def _search_serper(query: str, num_results: int = 10) -> list[dict]:
    """Call Serper Google search API and return normalised results."""
    if not SERPER_API_KEY:
        raise ValueError("SERPER_API_KEY not configured")

    payload = {"q": query, "num": num_results}
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(SERPER_BASE_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("organic", []):
        results.append(
            {
                "url": item.get("link", ""),
                "title": item.get("title", ""),
                "snippet": item.get("snippet", "")[:500],
                "publishedDate": item.get("date"),
            }
        )
    return results


async def _search_newsapi(query: str, num_results: int = 10) -> list[dict]:
    """Call NewsAPI everything endpoint and return normalised results."""
    if not NEWS_API_KEY:
        raise ValueError("NEWS_API_KEY not configured")

    from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "pageSize": num_results,
        "from": from_date,
        "language": "en",
        "apiKey": NEWS_API_KEY,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(NEWSAPI_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("articles", []):
        results.append(
            {
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "snippet": (item.get("description") or item.get("content") or "")[:500],
                "publishedDate": item.get("publishedAt"),
            }
        )
    return results


async def search_competitors(query: str) -> list[dict]:
    """Search for competitor candidates using Exa AI (falls back to Serper)."""
    try:
        results = await _search_exa(query)
        logger.info("Competitor search via Exa: %d results for query '%s'", len(results), query[:60])
        return results
    except Exception as exc:
        logger.warning("Exa search failed (%s), falling back to Serper", str(exc))

    try:
        results = await _search_serper(query)
        logger.info("Competitor search via Serper fallback: %d results for query '%s'", len(results), query[:60])
        return results
    except Exception as exc:
        logger.error("Serper fallback also failed: %s", str(exc))
        return []


async def search_news(query: str) -> list[dict]:
    """Search for news using Serper (falls back to Exa)."""
    try:
        results = await _search_serper(query)
        logger.info("News search via Serper: %d results for query '%s'", len(results), query[:60])
        return results
    except Exception as exc:
        logger.warning("Serper news search failed (%s), falling back to Exa", str(exc))

    try:
        results = await _search_exa(query)
        logger.info("News search via Exa fallback: %d results for query '%s'", len(results), query[:60])
        return results
    except Exception as exc:
        logger.error("Exa news fallback also failed: %s", str(exc))
        return []


async def searchCompetitorNews(competitor_name: str) -> list[dict]:
    """Search for news about a specific competitor using NewsAPI -> Serper -> Exa fallback chain."""
    try:
        results = await _search_newsapi(competitor_name)
        if results:
            logger.info("Competitor news search via NewsAPI: %d results for '%s'", len(results), competitor_name)
            return results
        logger.info("NewsAPI returned empty results for '%s', falling back to Serper", competitor_name)
    except Exception as exc:
        logger.warning("NewsAPI search failed (%s), falling back to Serper", str(exc))

    try:
        results = await _search_serper(f"{competitor_name} news")
        if results:
            logger.info("Competitor news search via Serper fallback: %d results for '%s'", len(results), competitor_name)
            return results
        logger.info("Serper returned empty results for '%s news', falling back to Exa", competitor_name)
    except Exception as exc:
        logger.warning("Serper news fallback failed (%s), falling back to Exa", str(exc))

    try:
        results = await _search_exa(f"latest news about {competitor_name}")
        logger.info("Competitor news search via Exa fallback: %d results for '%s'", len(results), competitor_name)
        return results
    except Exception as exc:
        logger.error("Exa news fallback also failed for '%s': %s", competitor_name, str(exc))
        return []


async def searchCompetitorActivity(competitor_name: str, activity_type: str) -> list[dict]:
    """Search for specific activity (funding, product launch, pricing, etc.) for a competitor using Serper -> NewsAPI fallback chain."""
    query = f"{competitor_name} {activity_type}"
    try:
        results = await _search_serper(query)
        if results:
            logger.info("Competitor activity search via Serper: %d results for '%s'", len(results), query)
            return results
        logger.info("Serper returned empty results for '%s', falling back to NewsAPI", query)
    except Exception as exc:
        logger.warning("Serper activity search failed (%s), falling back to NewsAPI", str(exc))

    try:
        results = await _search_newsapi(query)
        logger.info("Competitor activity search via NewsAPI fallback: %d results for '%s'", len(results), query)
        return results
    except Exception as exc:
        logger.error("NewsAPI activity fallback failed for '%s': %s", query, str(exc))
        return []

