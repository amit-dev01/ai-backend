"""
SearchService for Competitor Discovery Pipeline.

Provides two search provider integrations:
  - Exa AI (semantic search — primary for competitor discovery)
  - Serper (Google search — primary for news, fallback for competitors)

Each public function tries the primary provider first and falls back to
the secondary on any exception, ensuring maximum resilience.
"""

import logging
from typing import Optional

import httpx

from config import EXA_API_KEY, SERPER_API_KEY

logger = logging.getLogger(__name__)

EXA_BASE_URL = "https://api.exa.ai/search"
SERPER_BASE_URL = "https://google.serper.dev/search"

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
                "date": item.get("date", ""),
            }
        )
    return results


async def search_competitors(query: str) -> list[dict]:
    """Search for competitor candidates using Exa AI (falls back to Serper).

    Args:
        query: Semantic search query describing the competitor space.

    Returns:
        List of dicts with url, title, snippet fields.
        Returns empty list if both providers fail.
    """
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
    """Search for news using Serper (falls back to Exa).

    Args:
        query: News search query.

    Returns:
        List of dicts with url, title, snippet, date fields.
        Returns empty list if both providers fail.
    """
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
