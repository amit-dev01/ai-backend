"""
Machine Learning Anomaly Detection Service for Competitive Intelligence.

Uses scikit-learn's IsolationForest (Unsupervised Learning) to detect
statistically anomalous competitor moves against historical baselines:
  - Unusual PR & product activity surges
  - Sudden stealth periods / activity freezes
  - Sentiment crises and unexpected structural repricing

Features per observation vector:
  x = [event_volume, avg_impact_score, net_sentiment, price_points_count]
"""

import logging
from typing import Any, Optional
import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


class CompetitorAnomalyDetector:
    """Unsupervised Anomaly Detection using Isolation Forest."""

    @staticmethod
    def detect_anomalies(
        historical_features: list[list[float]],
        dates: list[str],
        competitor_name: str = "Competitor",
        contamination: float = 0.15,
    ) -> dict[str, Any]:
        """
        Fits an Isolation Forest model to historical feature vectors and flags anomalies.

        Args:
            historical_features: List of 4D vectors: [event_count, impact_score, sentiment, tier_count]
            dates: Corresponding date labels for each observation.
            competitor_name: Name of competitor.
            contamination: Expected proportion of outliers in the data.
        """
        n_samples = len(historical_features)
        if n_samples < 4:
            return {
                "competitorName": competitor_name,
                "hasAnomalies": False,
                "totalObservations": n_samples,
                "anomalies": [],
                "model": "IsolationForest (n_estimators=100)",
                "status": "INSUFFICIENT_DATA",
                "summary": f"Need at least 4 historical periods to fit IsolationForest (current: {n_samples})."
            }

        X = np.array(historical_features, dtype=float)

        # 1. Fit Unsupervised Isolation Forest
        # random_state=42 ensures reproducible deterministic predictions
        iso_forest = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42
        )
        iso_forest.fit(X)

        # Predictions: -1 for anomaly, 1 for normal
        preds = iso_forest.predict(X)
        # Decision function: lower values mean more anomalous
        scores = iso_forest.decision_function(X)

        anomalies_found = []
        means = np.mean(X, axis=0)

        for i in range(n_samples):
            if preds[i] == -1:  # Anomaly flagged
                date_label = dates[i] if i < len(dates) else f"Period-{i}"
                vec = X[i]
                anomaly_score = float(scores[i])

                # Determine Root Cause Characteristic
                # vec: [event_count, avg_impact, sentiment, tier_count]
                event_cnt, imp, sent, tiers = vec[0], vec[1], vec[2], vec[3]

                if event_cnt > (means[0] * 1.8):
                    anomaly_type = "VELOCITY_EXPANSION_ANOMALY"
                    desc = f"Activity volume spiked to {event_cnt:.0f} ({(event_cnt / max(means[0], 1.0)):.1f}x historical average)."
                elif event_cnt < (means[0] * 0.3) and means[0] >= 3:
                    anomaly_type = "UNUSUAL_STAGNATION_ANOMALY"
                    desc = f"Competitor went into unexpected silence: only {event_cnt:.0f} events recorded."
                elif sent < -0.5:
                    anomaly_type = "SENTIMENT_CRISIS_ANOMALY"
                    desc = f"Severe customer dissatisfaction event: sentiment dropped to {sent:+.2f}."
                elif imp >= 80.0:
                    anomaly_type = "HIGH_IMPACT_DISRUPTION"
                    desc = f"Statistically abnormal disruption event with impact score {imp:.0f}/100."
                else:
                    anomaly_type = "STRUCTURAL_MARKET_ANOMALY"
                    desc = f"Multivariate outlier detected across activity and pricing dimensions (Score: {anomaly_score:.3f})."

                anomalies_found.append({
                    "date": date_label,
                    "index": i,
                    "anomalyScore": round(anomaly_score, 3),
                    "anomalyType": anomaly_type,
                    "vector": {
                        "eventCount": int(event_cnt),
                        "avgImpact": round(imp, 1),
                        "sentiment": round(sent, 2),
                        "tierCount": int(tiers)
                    },
                    "description": desc,
                    "severity": "CRITICAL" if anomaly_score < -0.15 else "HIGH"
                })

        # Check if the latest period is currently anomalous
        is_latest_anomalous = bool(preds[-1] == -1)

        return {
            "competitorName": competitor_name,
            "hasAnomalies": len(anomalies_found) > 0,
            "isLatestPeriodAnomalous": is_latest_anomalous,
            "totalObservationsAnalyzed": n_samples,
            "totalAnomaliesDetected": len(anomalies_found),
            "anomalies": anomalies_found,
            "modelMetadata": {
                "algorithm": "IsolationForest",
                "n_estimators": 100,
                "contamination": contamination,
                "features": ["event_count", "avg_impact_score", "sentiment", "pricing_tiers_count"]
            },
            "summary": (
                f"Isolation Forest identified {len(anomalies_found)} statistical anomalies across {n_samples} periods. "
                + (f"Current period IS anomalous ({anomalies_found[-1]['anomalyType']})." if is_latest_anomalous else "Current state is within normal statistical distribution.")
            )
        }
