"""
Hugging Face Machine Learning Integration Service.

Connects to Hugging Face models for Competitive Intelligence:
  1. Semantic Similarity: 'sentence-transformers/all-MiniLM-L6-v2' (Dense Embeddings)
  2. Business Sentiment: 'ProsusAI/finbert' (Financial & Corporate Sentiment)

Architecture:
  - If HUGGINGFACE_API_KEY / HF_TOKEN is configured in environment:
      Calls hosted Hugging Face Serverless Inference API.
  - If no token is provided:
      Falls back to high-performance local vector cosine similarity via Scikit-Learn.
"""

import os
import logging
from typing import Any, Optional
import httpx
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Hugging Face Models
HF_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HF_SENTIMENT_MODEL = "ProsusAI/finbert"
HF_API_BASE = "https://router.huggingface.co/hf-inference/models"


class HuggingFaceService:
    """Hugging Face Model Inference with local Scikit-Learn mathematical fallback."""

    @staticmethod
    def _get_hf_token() -> Optional[str]:
        """Fetches HF token from environment if available."""
        return os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")

    @staticmethod
    async def compute_semantic_relevance(
        source_text: str,
        candidate_texts: list[str],
    ) -> dict[str, Any]:
        """
        Computes semantic relevance scores (0.0 to 1.0) between a source text
        (e.g., our company profile) and candidate competitor articles/pages.
        """
        if not candidate_texts:
            return {"scores": [], "model": "None"}

        token = HuggingFaceService._get_hf_token()

        # 1. Attempt Hugging Face Inference API if token is configured
        if token:
            try:
                url = f"{HF_API_BASE}/{HF_EMBEDDING_MODEL}"
                headers = {"Authorization": f"Bearer {token}"}
                payload = {
                    "inputs": {
                        "source_sentence": source_text[:1000],
                        "sentences": [c[:1000] for c in candidate_texts]
                    }
                }
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        scores = resp.json()
                        if isinstance(scores, list):
                            return {
                                "model": f"HuggingFace ({HF_EMBEDDING_MODEL})",
                                "isHostedInference": True,
                                "scores": [round(float(s), 3) for s in scores],
                                "method": "Dense 384-dimensional Sentence Embedding"
                            }
            except Exception as exc:
                logger.warning("Hugging Face API request failed, using local vector fallback: %s", exc)

        # 2. Local Mathematical Scikit-Learn Vector Space Fallback
        corpus = [source_text] + candidate_texts
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(corpus)

        # Cosine similarity between source (index 0) and all candidate texts (index 1 to end)
        sim_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        return {
            "model": "Local Scikit-Learn Vector Space (HF Fallback)",
            "isHostedInference": False,
            "scores": [round(float(s), 3) for s in sim_scores],
            "method": "TF-IDF N-Gram Cosine Similarity Matrix"
        }

    @staticmethod
    async def analyze_business_sentiment(text: str) -> dict[str, Any]:
        """
        Runs Financial/Corporate Sentiment Analysis via Hugging Face FinBERT model.
        """
        token = HuggingFaceService._get_hf_token()
        clean_text = text.strip()[:600]

        if token:
            try:
                url = f"{HF_API_BASE}/{HF_SENTIMENT_MODEL}"
                headers = {"Authorization": f"Bearer {token}"}
                payload = {"inputs": clean_text}

                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        # FinBERT returns [[{'label': 'positive', 'score': ...}, ...]]
                        if isinstance(data, list) and data and isinstance(data[0], list):
                            top_pred = max(data[0], key=lambda x: x.get("score", 0))
                            return {
                                "model": f"HuggingFace ({HF_SENTIMENT_MODEL})",
                                "isHostedInference": True,
                                "sentiment": top_pred.get("label", "neutral").upper(),
                                "confidence": round(float(top_pred.get("score", 0)), 3),
                                "distribution": data[0]
                            }
            except Exception as exc:
                logger.warning("Hugging Face FinBERT API call failed: %s", exc)

        # Deterministic Heuristic Fallback
        lower = clean_text.lower()
        pos_words = ["growth", "record", "profit", "launch", "breakthrough", "leader", "expanded", "win"]
        neg_words = ["layoffs", "lawsuit", "decline", "churn", "outage", "vulnerability", "loss", "struggle"]

        pos_count = sum(1 for w in pos_words if w in lower)
        neg_count = sum(1 for w in neg_words if w in lower)

        if pos_count > neg_count:
            sent, conf = "POSITIVE", round(0.65 + min(pos_count * 0.05, 0.25), 2)
        elif neg_count > pos_count:
            sent, conf = "NEGATIVE", round(0.65 + min(neg_count * 0.05, 0.25), 2)
        else:
            sent, conf = "NEUTRAL", 0.50

        return {
            "model": "Deterministic Business Sentiment Engine (HF Fallback)",
            "isHostedInference": False,
            "sentiment": sent,
            "confidence": conf,
            "distribution": [
                {"label": "positive", "score": 0.7 if sent == "POSITIVE" else 0.15},
                {"label": "negative", "score": 0.7 if sent == "NEGATIVE" else 0.15},
                {"label": "neutral", "score": 0.7 if sent == "NEUTRAL" else 0.15}
            ]
        }
