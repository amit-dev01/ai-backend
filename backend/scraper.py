"""
Scraper module for Competitor Analysis AI.

Uses Jina Reader (r.jina.ai) to scrape competitor websites and social media
profiles. Jina handles JavaScript rendering on their servers — no browser
or Playwright needed.

Cache policy: NO in-process file cache. All deduplication is handled by the
DB url_cache table via content-hash diffing in monitoring services. This
ensures monitoring always fetches fresh content for real change detection.
"""

import logging
import httpx

from config import JINA_API_KEY

logger = logging.getLogger(__name__)

JINA_BASE = "https://r.jina.ai/"

HEADERS = {
    "Accept": "text/markdown",
    "X-Return-Format": "markdown",
    "X-Remove-Selector": "header, footer, nav, .cookie-banner, .popup, script, style",
    "X-Retain-Images": "none",
}
if JINA_API_KEY:
    HEADERS["Authorization"] = f"Bearer {JINA_API_KEY}"


async def _direct_fallback_scrape(url: str) -> str:
    """Direct HTTP fallback using BeautifulSoup if Jina Reader fails or rate-limits."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")
    for el in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        el.decompose()

    text = soup.get_text(separator="\n", strip=True)
    if not text:
        raise Exception(f"Direct fallback scrape returned empty content for {url}")
    return text


async def scrape_website(url: str, bypass_cache: bool = False) -> str:
    """Scrape a competitor's website via Jina Reader with automatic direct fallback.

    Always fetches fresh content. First attempts Jina Reader (with full JS execution).
    If Jina fails, times out, or rate-limits, falls back directly to HTTP + BeautifulSoup.

    Args:
        url: The full URL of the website to scrape.
        bypass_cache: Kept for backward compatibility, has no effect.

    Returns:
        The scraped page content as Markdown or clean text.

    Raises:
        Exception: If both Jina and the direct fallback fail.
    """
    url_clean = url.strip()

    logger.info("Fetching via Jina Reader: %s", url_clean)
    jina_url = f"{JINA_BASE}{url_clean}"

    try:
        async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
            response = await client.get(jina_url, headers=HEADERS)
            response.raise_for_status()

        content = response.text.strip()
        if content:
            logger.info("Scraped %s via Jina — %d characters", url_clean, len(content))
            return content
    except Exception as exc:
        logger.warning("Jina Reader scrape failed for %s (%s). Attempting direct HTTP fallback...", url_clean, exc)

    # Fallback to direct scraping
    logger.info("Executing direct fallback scrape for: %s", url_clean)
    content = await _direct_fallback_scrape(url_clean)
    logger.info("Direct fallback scrape succeeded for %s — %d characters", url_clean, len(content))
    return content


async def scrape_social(url: str) -> str:
    """Best-effort scrape of a social media profile page via Jina Reader.

    Most social platforms block automated scraping, so this function
    catches all exceptions and returns an empty string on failure.

    Args:
        url: The social profile URL to attempt scraping.

    Returns:
        Up to 8000 characters of Markdown content, or an empty string on failure.
    """
    logger.info("Attempting social scrape via Jina: %s", url)

    try:
        jina_url = f"{JINA_BASE}{url}"

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(jina_url, headers=HEADERS)
            response.raise_for_status()

        content = response.text.strip()[:8000]

        if not content:
            logger.warning("Jina returned no content for %s", url)
            return ""

        logger.info("Social scrape complete: %s — %d characters", url, len(content))
        return content

    except Exception as e:
        logger.warning("Social scrape failed for %s: %s", url, str(e))
        return ""
