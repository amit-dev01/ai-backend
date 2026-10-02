"""
SearchService for Competitor Discovery Pipeline.

Provides two search provider integrations:
  - Exa AI (semantic search — primary for competitor discovery)
  - Serper (Google search — primary for news, fallback for competitors)
  - NewsAPI (news articles — primary for competitor news feed)

Each public function tries the primary provider first and falls back to
the secondary on any exception, ensuring maximum resilience.

Key improvements:
  - News searches include the competitor name in quotes for exact matching
  - News results pre-filtered for title relevance before returning
  - Competitor discovery uses site-specific Serper search to find homepages
  - Serper news search uses Google News endpoint (tbs=qdr:m) for fresh results
"""

from datetime import datetime, timedelta
import logging
from typing import Optional
from urllib.parse import urlparse

import httpx

from config import EXA_API_KEY, SERPER_API_KEY, NEWS_API_KEY

logger = logging.getLogger(__name__)

EXA_BASE_URL = "https://api.exa.ai/search"
SERPER_BASE_URL = "https://google.serper.dev/search"
SERPER_NEWS_URL = "https://google.serper.dev/news"
NEWSAPI_BASE_URL = "https://newsapi.org/v2/everything"

BLOCKED_DOMAINS = {
    "wikipedia.org",
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "youtube.com",
    "reddit.com",
    "tiktok.com",
    "pinterest.com",
    "quora.com",
}

# Domains that produce irrelevant or generic content for news monitoring
NOISE_DOMAINS = {
    "g2.com",
    "capterra.com",
    "trustpilot.com",
    "getapp.com",
    "softwareadvice.com",
    "glassdoor.com",
    "indeed.com",
    "crunchbase.com",
    "ycombinator.com",
    "techcrunch.com",   # keep as news — removed from noise, generic only
}

# Domains that are useful for news but not for discovery
NEWS_OK_DOMAINS = {
    "techcrunch.com",
    "venturebeat.com",
    "businessinsider.com",
    "forbes.com",
    "reuters.com",
    "bloomberg.com",
    "wsj.com",
    "ft.com",
    "wired.com",
    "theverge.com",
    "zdnet.com",
}


def _extract_domain(url: str) -> str:
    """Extract root domain from URL."""
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        host = parsed.netloc.lower()
        return host.lstrip("www.")
    except Exception:
        return url.lower()


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


def _title_mentions_competitor(title: str, competitor_name: str) -> bool:
    """Check if a news article title plausibly mentions the competitor.

    Uses word-boundary check: the competitor name or any significant word
    from it must appear in the title (case-insensitive).
    """
    if not title or not competitor_name:
        return False

    title_lower = title.lower()
    comp_lower = competitor_name.lower().strip()

    # Full name match
    if comp_lower in title_lower:
        return True

    # Partial match: any word > 4 chars from competitor name must appear
    words = [w for w in comp_lower.split() if len(w) > 4]
    return any(w in title_lower for w in words)


async def _search_exa(query: str, num_results: int = 10, category: str = "") -> list[dict]:
    """Call Exa AI semantic search API and return normalised results.

    Args:
        query: Search query string.
        num_results: Max results to request.
        category: Optional Exa category filter ('company', 'news', etc.)
    """
    if not EXA_API_KEY:
        raise ValueError("EXA_API_KEY not configured")

    payload = {
        "query": query,
        "numResults": num_results,
        "useAutoprompt": True,
        "contents": {"text": True},
    }
    if category:
        payload["category"] = category

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.post(EXA_BASE_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "snippet": (item.get("text") or item.get("snippet") or "")[:600],
                "publishedDate": item.get("publishedDate") or item.get("date"),
            }
        )
    return results


async def _search_serper(query: str, num_results: int = 10) -> list[dict]:
    """Call Serper Google search API (organic results) and return normalised results."""
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
                "snippet": item.get("snippet", "")[:600],
                "publishedDate": item.get("date"),
            }
        )
    return results


async def _search_serper_news(query: str, num_results: int = 10) -> list[dict]:
    """Call Serper Google News endpoint for fresh news articles.

    This uses the /news endpoint which is tuned for news articles and
    returns more recent results than the organic search endpoint.
    """
    if not SERPER_API_KEY:
        raise ValueError("SERPER_API_KEY not configured")

    payload = {"q": query, "num": num_results}
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(SERPER_NEWS_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("news", []):
        results.append(
            {
                "url": item.get("link", ""),
                "title": item.get("title", ""),
                "snippet": item.get("snippet", "")[:600],
                "publishedDate": item.get("date"),
                "source": item.get("source", ""),
            }
        )
    return results


async def _search_newsapi(query: str, num_results: int = 10) -> list[dict]:
    """Call NewsAPI everything endpoint and return normalised results.

    Uses exact phrase matching by quoting the query to reduce noise.
    """
    if not NEWS_API_KEY:
        raise ValueError("NEWS_API_KEY not configured")

    from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    params = {
        "q": query,
        "sortBy": "relevancy",   # relevancy > publishedAt for better matching
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
                "snippet": (item.get("description") or item.get("content") or "")[:600],
                "publishedDate": item.get("publishedAt"),
                "source": item.get("source", {}).get("name", ""),
            }
        )
    return results


async def search_competitors(query: str) -> list[dict]:
    """Search for competitor candidates using Exa AI with 'company' category hint.

    Uses Exa's company category for better homepage discovery.
    Falls back to Serper with site-restricted queries.
    """
    try:
        results = await _search_exa(query, num_results=10, category="company")
        logger.info("Competitor search via Exa: %d results for query '%s'", len(results), query[:60])
        return results
    except Exception as exc:
        logger.warning("Exa search failed (%s), falling back to Serper", str(exc))

    try:
        # Serper fallback: add -site: exclusions to avoid review/comparison sites
        clean_query = f"{query} -site:g2.com -site:capterra.com -site:getapp.com -site:reddit.com"
        results = await _search_serper(clean_query)
        logger.info("Competitor search via Serper fallback: %d results for query '%s'", len(results), query[:60])
        return results
    except Exception as exc:
        logger.error("Serper fallback also failed: %s", str(exc))
        return []


async def search_news(query: str) -> list[dict]:
    """Search for news using Serper News (falls back to Exa).

    Primary: Serper /news endpoint (Google News — more recent)
    Fallback: Exa semantic news search
    """
    try:
        results = await _search_serper_news(query)
        logger.info("News search via Serper News: %d results for query '%s'", len(results), query[:60])
        return results
    except Exception as exc:
        logger.warning("Serper News search failed (%s), falling back to Exa", str(exc))

    try:
        results = await _search_exa(query)
        logger.info("News search via Exa fallback: %d results for query '%s'", len(results), query[:60])
        return results
    except Exception as exc:
        logger.error("Exa news fallback also failed: %s", str(exc))
        return []


async def searchCompetitorNews(competitor_name: str) -> list[dict]:
    """Search for news about a specific competitor.

    Strategy:
    1. NewsAPI with exact quoted name + relevance sort (most precise)
    2. Serper /news with quoted name (Google News, very fresh)
    3. Exa semantic fallback

    All results are pre-filtered: title must mention the competitor name.
    """
    # Build exact-match queries — quoted name dramatically reduces noise
    exact_query = f'"{competitor_name}"'

    # 1. NewsAPI with exact name match
    try:
        raw = await _search_newsapi(exact_query, num_results=10)
        results = [r for r in raw if _title_mentions_competitor(r.get("title", ""), competitor_name)]
        if results:
            logger.info(
                "Competitor news via NewsAPI: %d/%d relevant for '%s'",
                len(results), len(raw), competitor_name,
            )
            return results
        logger.info("NewsAPI: no relevant results for '%s', trying Serper News", competitor_name)
    except Exception as exc:
        logger.warning("NewsAPI failed (%s), trying Serper News", str(exc))

    # 2. Serper /news with exact name
    try:
        raw = await _search_serper_news(f'"{competitor_name}" news')
        results = [r for r in raw if _title_mentions_competitor(r.get("title", ""), competitor_name)]
        if results:
            logger.info(
                "Competitor news via Serper News: %d/%d relevant for '%s'",
                len(results), len(raw), competitor_name,
            )
            return results
        logger.info("Serper News: no relevant results for '%s', trying Exa", competitor_name)
    except Exception as exc:
        logger.warning("Serper News failed (%s), trying Exa", str(exc))

    # 3. Exa fallback
    try:
        raw = await _search_exa(f"latest news about {competitor_name}")
        results = [r for r in raw if _title_mentions_competitor(r.get("title", ""), competitor_name)]
        logger.info(
            "Competitor news via Exa fallback: %d/%d relevant for '%s'",
            len(results), len(raw), competitor_name,
        )
        return results
    except Exception as exc:
        logger.error("All news search providers failed for '%s': %s", competitor_name, str(exc))
        return []


async def searchCompetitorActivity(competitor_name: str, activity_type: str) -> list[dict]:
    """Search for specific competitor activity (funding, product launch, etc.).

    Uses exact competitor name in quotes + activity type for precision.
    All results pre-filtered: title must mention the competitor.

    Strategy:
    1. Serper /news (Google News — most current)
    2. NewsAPI fallback
    """
    # Quoted name + activity type = high precision query
    query = f'"{competitor_name}" {activity_type}'

    # 1. Serper News
    try:
        raw = await _search_serper_news(query, num_results=10)
        results = [r for r in raw if _title_mentions_competitor(r.get("title", ""), competitor_name)]
        if results:
            logger.info(
                "Activity search via Serper News: %d/%d relevant for '%s %s'",
                len(results), len(raw), competitor_name, activity_type,
            )
            return results
        # If no results with quoted name, try without quotes (broader)
        raw2 = await _search_serper_news(f"{competitor_name} {activity_type}", num_results=10)
        results2 = [r for r in raw2 if _title_mentions_competitor(r.get("title", ""), competitor_name)]
        if results2:
            logger.info(
                "Activity search (broad) via Serper News: %d/%d relevant",
                len(results2), len(raw2),
            )
            return results2
        logger.info("Serper News: no relevant results for '%s', trying NewsAPI", query)
    except Exception as exc:
        logger.warning("Serper News activity search failed (%s), trying NewsAPI", str(exc))

    # 2. NewsAPI fallback
    try:
        raw = await _search_newsapi(f"{competitor_name} {activity_type}", num_results=10)
        results = [r for r in raw if _title_mentions_competitor(r.get("title", ""), competitor_name)]
        logger.info(
            "Activity search via NewsAPI fallback: %d/%d relevant for '%s %s'",
            len(results), len(raw), competitor_name, activity_type,
        )
        return results
    except Exception as exc:
        logger.error("All providers failed for activity search '%s %s': %s", competitor_name, activity_type, str(exc))
        return []
