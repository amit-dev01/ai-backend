"""
Scraper module for Competitor Analysis AI.

Uses Jina Reader (r.jina.ai) to scrape competitor websites and social media
profiles. Jina handles JavaScript rendering on their servers — no browser
or Playwright needed.
"""

import logging
import httpx

import time
import json
from pathlib import Path
from config import JINA_API_KEY

logger = logging.getLogger(__name__)

JINA_BASE = "https://r.jina.ai/"

HEADERS = {
    "Accept": "text/markdown",
    "X-Return-Format": "markdown",
}
if JINA_API_KEY:
    HEADERS["Authorization"] = f"Bearer {JINA_API_KEY}"

CACHE_TTL_SECONDS = 7 * 24 * 3600  # 7 days
_CACHE_FILE = Path(__file__).parent / ".jina_cache.json"
_JINA_CACHE: dict[str, tuple[float, str]] = {}


def _load_cache():
    global _JINA_CACHE
    if _CACHE_FILE.exists():
        try:
            data = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
            _JINA_CACHE = {k: (float(v[0]), str(v[1])) for k, v in data.items()}
            logger.info("Loaded %d cached Jina scrape entries", len(_JINA_CACHE))
        except Exception as e:
            logger.warning("Failed to load Jina cache file: %s", e)


def _save_cache():
    try:
        data = {k: [v[0], v[1]] for k, v in _JINA_CACHE.items()}
        _CACHE_FILE.write_text(json.dumps(data), encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to save Jina cache file: %s", e)


_load_cache()


async def scrape_website(url: str) -> str:
    """Scrape a competitor's website via Jina Reader and return Markdown.

    Includes a 7-day cache to avoid re-fetching recently scraped URLs.

    Args:
        url: The full URL of the website to scrape.

    Returns:
        The scraped page content as Markdown.

    Raises:
        Exception: If the request fails or returns no content.
    """
    url_clean = url.strip()
    now = time.time()

    if url_clean in _JINA_CACHE:
        cached_time, content = _JINA_CACHE[url_clean]
        if now - cached_time < CACHE_TTL_SECONDS:
            logger.info("Using cached Jina scrape for %s (%d chars)", url_clean, len(content))
            return content

    logger.info("Starting website scrape via Jina: %s", url_clean)
    jina_url = f"{JINA_BASE}{url_clean}"

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(jina_url, headers=HEADERS)
        response.raise_for_status()

    content = response.text.strip()

    if not content:
        raise Exception(f"Jina returned empty content for {url_clean}")

    _JINA_CACHE[url_clean] = (now, content)
    _save_cache()

    logger.info(
        "Website scrape complete: %s — %d characters extracted", url_clean, len(content)
    )
    return content


async def scrape_social(url: str) -> str:
    """Best-effort scrape of a social media profile page via Jina Reader.

    Most social platforms block automated scraping, so this function
    catches all exceptions and returns an empty string on failure.

    Args:
        url: The social profile URL to attempt scraping.

    Returns:
        Up to 5000 characters of Markdown content, or an empty string on failure.
    """
    logger.info("Attempting social scrape via Jina: %s", url)

    try:
        jina_url = f"{JINA_BASE}{url}"

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(jina_url, headers=HEADERS)
            response.raise_for_status()

        content = response.text.strip()[:5000]

        if not content:
            logger.warning("Jina returned no content for %s", url)
            return ""

        logger.info(
            "Social scrape complete: %s — %d characters extracted", url, len(content)
        )
        return content

    except Exception as e:
        logger.warning("Social scrape failed for %s: %s", url, str(e))
        return ""
