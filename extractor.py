"""
Extractor module for Competitor Analysis AI.

Uses Groq LLM to extract structured business intelligence signals
from raw scraped website content.
"""

import json
import logging
from datetime import date

from openai import AsyncOpenAI

from config import GROQ_API_KEY, GROQ_BASE_URL, EXTRACTION_MODEL
from prompts import EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)


async def extract_signals(scraped_text: str, company_name: str) -> dict:
    """Extract structured competitor data from raw scraped content using an LLM.

    Content is capped at 25,000 characters. Groq's llama-3.1-8b-instant
    supports 128k context — we use ~6k tokens for content leaving ample
    room for the prompt + response while capturing far more signal than
    the old 8k char cap.

    Args:
        scraped_text: Raw Markdown content from the website/social scrape.
        company_name: Name of the competitor being analyzed.

    Returns:
        A rich dictionary of extracted structured signals.
    """
    logger.info("Starting deep signal extraction for %s (%d chars total)", company_name, len(scraped_text))

    # 25k chars ≈ ~6,250 tokens — well within Groq's 128k context window
    capped_content = scraped_text[:25000]

    user_prompt = EXTRACTION_PROMPT.format(scraped_content=capped_content)

    response = await client.chat.completions.create(
        model=EXTRACTION_MODEL,
        messages=[{"role": "user", "content": user_prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    raw_output = response.choices[0].message.content
    extracted = json.loads(raw_output)

    logger.info(
        "Signal extraction complete for %s — %d top-level keys extracted",
        company_name,
        len(extracted),
    )
    return extracted
