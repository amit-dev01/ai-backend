"""
Scraper module for Competitor Analysis AI.

Uses Jina Reader (r.jina.ai) to scrape competitor websites and social media
profiles. Jina handles JavaScript rendering on their servers — no browser
or Playwright needed.
"""

import logging
import httpx

logger = logging.getLogger(__name__)

JINA_BASE = "https://r.jina.ai/"

HEADERS = {
    "Accept": "text/markdown",
    "X-Return-Format": "markdown",
}


async def scrape_website(url: str) -> str:
    """Scrape a competitor's website via Jina Reader and return Markdown.

    Args:
        url: The full URL of the website to scrape.

    Returns:
        The scraped page content as Markdown.

    Raises:
        Exception: If the request fails or returns no content.
    """
    logger.info("Starting website scrape via Jina: %s", url)

    jina_url = f"{JINA_BASE}{url}"

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(jina_url, headers=HEADERS)
        response.raise_for_status()

    content = response.text.strip()

    if not content:
        raise Exception(f"Jina returned empty content for {url}")

    logger.info(
        "Website scrape complete: %s — %d characters extracted", url, len(content)
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
