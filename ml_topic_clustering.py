"""
Machine Learning Topic Clustering Service for Competitive Intelligence.

Uses Unsupervised Machine Learning:
  - TfidfVectorizer for high-dimensional text feature representation
  - KMeans Clustering (k=3 or 4) to group competitor intelligence events
  - Centroid Feature Inspection to automatically label strategic market themes
"""

import logging
from typing import Any, Optional
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

# Stopwords specific to corporate press releases
STOPWORDS = "english"


class TopicClusteringEngine:
    """Unsupervised K-Means clustering over competitive intelligence documents."""

    @staticmethod
    def cluster_intelligence_documents(
        documents: list[dict[str, Any]],
        num_clusters: int = 3,
    ) -> dict[str, Any]:
        """
        Clusters competitive documents into strategic thematic groups using KMeans.

        Args:
            documents: List of dicts containing 'title', 'summary', 'competitor_name', 'impact_score'.
            num_clusters: Number of clusters (k).
        """
        if not documents or len(documents) < 3:
            return {
                "totalDocuments": len(documents),
                "numClusters": 0,
                "clusters": [],
                "status": "INSUFFICIENT_DATA",
                "summary": "Need at least 3 documents to perform unsupervised KMeans clustering."
            }

        k = min(num_clusters, max(2, len(documents) // 2))

        # 1. Build text corpus
        corpus = [
            f"{d.get('title', '')} {d.get('summary', '')}"
            for d in documents
        ]

        # 2. Vectorize using TF-IDF
        try:
            vectorizer = TfidfVectorizer(
                stop_words=STOPWORDS,
                ngram_range=(1, 2),
                max_features=100,
                min_df=1
            )
            X = vectorizer.fit_transform(corpus)
            feature_names = vectorizer.get_feature_names_out()

            # 3. Fit KMeans Clustering
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X)

            labels = kmeans.labels_
            centroids = kmeans.cluster_centers_

        except Exception as exc:
            logger.error("KMeans clustering execution error: %s", exc)
            return {
                "totalDocuments": len(documents),
                "numClusters": 0,
                "clusters": [],
                "status": "ERROR",
                "message": str(exc)
            }

        # 4. Extract Top Terms per Cluster Centroid
        clusters_output = []
        for i in range(k):
            # Sort centroid weights descending
            top_term_indices = centroids[i].argsort()[::-1][:5]
            top_terms = [feature_names[idx] for idx in top_term_indices if centroids[i][idx] > 0]
            
            # Map assigned documents
            assigned_docs = [
                {
                    "title": documents[idx].get("title", ""),
                    "competitor": documents[idx].get("competitor_name", ""),
                    "impactScore": documents[idx].get("impact_score", 50),
                    "summary": documents[idx].get("summary", "")[:120] + "..."
                }
                for idx in range(len(documents)) if labels[idx] == i
            ]

            # Strategic Theme Derivation
            theme_keywords_lower = " ".join(top_terms).lower()
            if any(w in theme_keywords_lower for w in ["ai", "model", "agent", "api", "cloud", "engine", "feature"]):
                strategic_label = "Product & AI Innovation"
            elif any(w in theme_keywords_lower for w in ["price", "pricing", "cost", "plan", "tier", "free", "user"]):
                strategic_label = "Monetization & Pricing Moves"
            elif any(w in theme_keywords_lower for w in ["hire", "ceo", "vp", "growth", "expand", "partner", "acquire"]):
                strategic_label = "GTM & Leadership Expansion"
            elif any(w in theme_keywords_lower for w in ["security", "compliance", "soc2", "enterprise", "audit"]):
                strategic_label = "Enterprise Governance & Security"
            else:
                strategic_label = f"Cluster {i+1}: " + ", ".join(top_terms[:2]).title()

            doc_pct = round((len(assigned_docs) / len(documents)) * 100.0, 1)

            clusters_output.append({
                "clusterId": i,
                "theme": strategic_label,
                "topKeyphrases": top_terms,
                "documentCount": len(assigned_docs),
                "categorySharePct": doc_pct,
                "sampleDocuments": assigned_docs[:3]
            })

        # Sort clusters by document share % descending
        clusters_output.sort(key=lambda c: c["categorySharePct"], reverse=True)

        return {
            "totalDocumentsClustered": len(documents),
            "kClusters": k,
            "algorithm": "KMeans (TF-IDF Vector Space)",
            "dominantTheme": clusters_output[0]["theme"] if clusters_output else "N/A",
            "clusters": clusters_output,
            "summary": (
                f"K-Means grouped {len(documents)} intelligence events into {k} clusters. "
                f"The dominant competitive focus is '{clusters_output[0]['theme']}' "
                f"({clusters_output[0]['categorySharePct']}% of total events)."
            )
        }
