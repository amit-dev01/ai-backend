"""
NLP Portfolio Engine for Competitive Intelligence.

Implements mathematical and classical NLP techniques:
  1. Flagship Product Identification:
     - TF-IDF N-Gram Prominence over DOM headers and scraped content.
     - Identifies the anchor/flagship offering vs secondary tools.
  2. Market Boundary Extraction:
     - Price Minima (Freemium/Entry floor).
     - Price Maxima (Enterprise ceiling).
     - Median pricing and detected tier breakdown.
  3. Category White Space Analysis:
     - Mathematical gap detection between competitor pricing tiers.
"""

import logging
import re
from typing import Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

# Stopwords specific to corporate marketing jargon
DOMAIN_STOPWORDS = {
    "software", "platform", "solution", "solutions", "tool", "tools",
    "service", "services", "system", "business", "company", "help",
    "helps", "features", "products", "free", "trial", "privacy", "terms",
    "cookie", "cookies", "policy", "login", "sign", "signup", "contact",
    "sales", "demo", "overview", "started", "learn", "more", "click",
    "best", "better", "great", "new", "world", "management", "experience"
}


def extract_flagship_and_boundaries(
    content: str,
    headers_text: Optional[str] = None,
    competitor_name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Analyzes competitor web content to deterministically extract:
      1. Flagship Product Anchor (via TF-IDF n-gram salience on headers & body)
      2. Pricing Boundaries: Minima, Maxima, Median
      3. Product Portfolio Hierarchy
    """
    if not content or len(content.strip()) < 50:
        return {
            "flagshipProduct": competitor_name or "Core Platform",
            "productKeywords": [],
            "priceMinima": None,
            "priceMaxima": None,
            "priceMedian": None,
            "pricingTiersFound": [],
            "whiteSpaceOpportunity": None,
        }

    # -----------------------------------------------------------------
    # 1. NLP TF-IDF Flagship Extraction
    # -----------------------------------------------------------------
    # Emphasize headings and title text by repeating them in the corpus
    analysis_corpus = []
    if headers_text and len(headers_text.strip()) > 5:
        # Heavily weight headers (3x)
        analysis_corpus.append(headers_text.lower())
        analysis_corpus.append(headers_text.lower())
        analysis_corpus.append(headers_text.lower())
    
    # Chunk main content into paragraph segments
    paragraphs = [p.strip().lower() for p in content.split("\n") if len(p.strip()) > 20]
    analysis_corpus.extend(paragraphs[:30])

    flagship_candidates = []
    try:
        # Extract 2-gram and 3-gram keyphrases
        vectorizer = TfidfVectorizer(
            ngram_range=(2, 3),
            stop_words="english",
            max_features=40,
            min_df=1,
        )
        tfidf_matrix = vectorizer.fit_transform(analysis_corpus)
        feature_names = vectorizer.get_feature_names_out()
        scores = np.asarray(tfidf_matrix.sum(axis=0)).ravel()

        # Sort candidate phrases by cumulative TF-IDF score
        ranked_indices = scores.argsort()[::-1]
        
        comp_clean = (competitor_name or "").lower()
        for idx in ranked_indices:
            phrase = feature_names[idx]
            words = phrase.split()
            # Filter out generic jargon
            if any(w in DOMAIN_STOPWORDS for w in words):
                continue
            if len(phrase) < 4:
                continue
            # Capitalize nicely
            title_phrase = " ".join(w.capitalize() for w in words)
            if title_phrase not in flagship_candidates:
                flagship_candidates.append(title_phrase)
                if len(flagship_candidates) >= 5:
                    break
    except Exception as exc:
        logger.warning("TF-IDF flagship extraction warning: %s", exc)

    flagship_product = flagship_candidates[0] if flagship_candidates else f"{competitor_name or 'Core'} Suite"

    # -----------------------------------------------------------------
    # 2. Mathematical Price Minima, Maxima & Tiers Extraction
    # -----------------------------------------------------------------
    # Pattern looks for $XX or $XX/mo, $XX/month, $XX per user
    price_patterns = re.findall(
        r"(?:[\$€£]\s?([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?))",
        content
    )

    numeric_prices: list[float] = []
    for raw_p in price_patterns:
        try:
            val = float(raw_p.replace(",", ""))
            # Sanity check: filter out years (2024, 2025, 2026) or penny fractions
            if 5.0 <= val <= 5000.0 and val not in (2020.0, 2021.0, 2022.0, 2023.0, 2024.0, 2025.0, 2026.0):
                numeric_prices.append(val)
        except ValueError:
            continue

    numeric_prices = sorted(list(set(numeric_prices)))

    price_minima = float(numeric_prices[0]) if numeric_prices else None
    price_maxima = float(numeric_prices[-1]) if numeric_prices else None
    price_median = float(np.median(numeric_prices)) if numeric_prices else None

    # Check for freemium / free tier presence
    has_free_tier = bool(re.search(r"\b(free tier|forever free|free plan|\$0)\b", content, re.IGNORECASE))
    if has_free_tier and (price_minima is None or price_minima > 0):
        price_minima = 0.0

    # -----------------------------------------------------------------
    # 3. White Space Analysis
    # -----------------------------------------------------------------
    white_space = None
    if len(numeric_prices) >= 2:
        # Find the largest gap between consecutive tiers
        diffs = [numeric_prices[i+1] - numeric_prices[i] for i in range(len(numeric_prices)-1)]
        max_diff_idx = int(np.argmax(diffs))
        gap_start = numeric_prices[max_diff_idx]
        gap_end = numeric_prices[max_diff_idx + 1]
        if (gap_end - gap_start) >= 20.0:
            white_space = f"Uncontested pricing gap between ${gap_start:.0f} and ${gap_end:.0f}/mo"

    return {
        "flagshipProduct": flagship_product,
        "productKeywords": flagship_candidates,
        "priceMinima": price_minima,
        "priceMaxima": price_maxima,
        "priceMedian": price_median,
        "pricingTiersFound": [f"${p:.0f}" for p in numeric_prices[:6]],
        "hasFreeTier": has_free_tier,
        "whiteSpaceOpportunity": white_space,
    }
