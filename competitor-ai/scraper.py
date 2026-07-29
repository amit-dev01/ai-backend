"""
Scraper module for Competitor Analysis AI.

Uses Crawl4AI's AsyncWebCrawler to scrape competitor websites and social media
profiles asynchronously. Social scraping is best-effort — most platforms block
automated access.
"""

import logging
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

logger = logging.getLogger(__name__)


async def scrape_website(url: str) -> str:
    """Scrape a competitor's website and return the content as Markdown.

    Args:
        url: The full URL of the website to scrape.

    Returns:
        The scraped page content converted to Markdown.

    Raises:
        Exception: If the crawl fails or returns no content.
    """
    logger.info("Starting website scrape: %s", url)

    config = CrawlerRunConfig(
        word_count_threshold=10,
        exclude_external_links=True,
        remove_overlay_elements=True,
        process_iframes=False,
    )

    browser_config = BrowserConfig(browser_type="chromium", channel="msedge")
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=config)

        if not result.success:
            error_msg = f"Failed to scrape {url}: {result.error_message}"
            logger.error(error_msg)
            raise Exception(error_msg)

        markdown_content = result.markdown or ""
        if not markdown_content.strip():
            error_msg = f"Scrape returned empty content for {url}"
            logger.error(error_msg)
            raise Exception(error_msg)

        logger.info(
            "Website scrape complete: %s — %d characters extracted",
            url,
            len(markdown_content),
        )
        return markdown_content


async def scrape_social(url: str) -> str:
    """Best-effort scrape of a social media profile page.

    Most social platforms block automated scraping, so this function
    catches all exceptions and returns an empty string on failure.

    Args:
        url: The social profile URL to attempt scraping.

    Returns:
        Up to 5000 characters of Markdown content, or an empty string on failure.
    """
    logger.info("Attempting social scrape: %s", url)

    try:
        config = CrawlerRunConfig(
            word_count_threshold=10,
            exclude_external_links=True,
            remove_overlay_elements=True,
            process_iframes=False,
        )

        browser_config = BrowserConfig(browser_type="chromium", channel="msedge")
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=config)

            if not result.success or not result.markdown:
                logger.warning("Social scrape returned no content for %s", url)
                return ""

            content = result.markdown[:5000]
            logger.info(
                "Social scrape complete: %s — %d characters extracted",
                url,
                len(content),
            )
            return content

    except Exception as e:
        logger.warning("Social scrape failed for %s: %s", url, str(e))
        return ""
