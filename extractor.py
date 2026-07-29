"""
Extractor module for Competitor Analysis AI.

Uses an LLM (via Groq's OpenAI-compatible API) to extract structured business
intelligence signals from raw scraped website content.
"""

import json
import logging

from openai import AsyncOpenAI

from config import GROQ_API_KEY, GROQ_BASE_URL, EXTRACTION_MODEL
from prompts import EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)


async def extract_signals(scraped_text: str, company_name: str) -> dict:
    """Extract structured competitor data from raw scraped content using an LLM.

    The scraped text is capped at 50,000 characters to stay within token limits.
    The LLM returns a structured JSON object containing company basics, products,
    pricing, positioning, marketing signals, tech signals, and more.

    Args:
        scraped_text: Raw Markdown content from the website/social scrape.
        company_name: Name of the competitor being analyzed.

    Returns:
        A dictionary of extracted structured signals (company_basics,
        products_and_services, pricing_strategy, etc.).
    """
    logger.info("Starting signal extraction for %s", company_name)

    # Cap content to stay within Groq free-tier TPM limits (~6000 TPM)
    # ~8000 chars ≈ ~2000 tokens, leaving room for prompt + response
    capped_content = scraped_text[:8000]

    user_prompt = EXTRACTION_PROMPT.format(scraped_content=capped_content)

    response = await client.chat.completions.create(
        model=EXTRACTION_MODEL,
        messages=[
            {
                "role": "user",
                "content": user_prompt,
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    raw_output = response.choices[0].message.content
    extracted = json.loads(raw_output)

    logger.info(
        "Signal extraction complete for %s — %d top-level keys",
        company_name,
        len(extracted),
    )
    return extracted
