"""
Signal Processing & Anomaly Analyzer for Competitive Intelligence.

Applies mathematical signal processing:
  1. Local Maxima Detection (find_peaks):
     - Activity spikes, product launch waves, funding announcement peaks.
  2. Local Minima Detection (troughs):
     - Sentiment drops, prolonged quiet periods / stealth development.
  3. Signal Volatility & Momentum:
     - Standard deviation (noise floor) and directional momentum vectors.
"""

import logging
from typing import Any, Optional
import numpy as np
from scipy.signal import find_peaks

logger = logging.getLogger(__name__)


def analyze_competitor_signal(
    event_counts: list[int],
    dates: list[str],
    sentiment_scores: Optional[list[float]] = None,
    competitor_name: str = "Competitor",
) -> dict[str, Any]:
    """
    Applies mathematical signal processing to competitor historical events:
      - Uses scipy.signal.find_peaks to find activity peaks (maxima)
      - Inverts signal to find quiet stagnation troughs (minima)
      - Detects sentiment minima (potential churn inflection points)
      - Computes momentum (accelerating vs decelerating)
    """
    if not event_counts or len(event_counts) < 2:
        return {
            "maxima": [],
            "minima": [],
            "volatility": 0.0,
            "momentum": "STABLE",
            "currentStatus": "NORMAL",
            "summary": f"{competitor_name} has baseline market activity.",
        }

    signal = np.array(event_counts, dtype=float)
    n = len(signal)
    mean_val = float(np.mean(signal))
    std_val = float(np.std(signal)) if float(np.std(signal)) > 0 else 1.0

    # Prominence threshold: peak must stand out by at least 1.0 std or min 1.5 events
    prominence_thresh = max(1.0, std_val * 0.8)

    # 1. Detect Local Maxima (Activity Peaks)
    # distance=2 ensures separate distinct events
    peaks, peak_props = find_peaks(signal, distance=1, prominence=prominence_thresh)

    maxima_events = []
    for idx in peaks:
        val = int(signal[idx])
        date_label = dates[idx] if idx < len(dates) else f"T-{n - idx}"
        severity = "CRITICAL_SPIKE" if (signal[idx] - mean_val) >= (2 * std_val) else "HIGH_ACTIVITY"
        maxima_events.append({
            "index": int(idx),
            "date": date_label,
            "eventVolume": val,
            "type": "LOCAL_MAXIMA",
            "severity": severity,
            "description": f"Activity surge at {date_label}: {val} events ({val - mean_val:+.1f} above avg)",
        })

    # 2. Detect Local Minima (Activity Troughs / Quiet Periods)
    # We invert the signal: peaks in -signal correspond to valleys in signal
    troughs, _ = find_peaks(-signal, distance=1, prominence=prominence_thresh)

    minima_events = []
    for idx in troughs:
        val = int(signal[idx])
        date_label = dates[idx] if idx < len(dates) else f"T-{n - idx}"
        minima_events.append({
            "index": int(idx),
            "date": date_label,
            "eventVolume": val,
            "type": "LOCAL_MINIMA",
            "severity": "LOW_ACTIVITY",
            "description": f"Activity trough at {date_label}: only {val} events recorded",
        })

    # 3. Sentiment Minima (Customer dissatisfaction inflection points)
    sentiment_anomalies = []
    if sentiment_scores and len(sentiment_scores) >= 2:
        sent_arr = np.array(sentiment_scores, dtype=float)
        # Invert sentiment to find drops/troughs
        sent_troughs, _ = find_peaks(-sent_arr, distance=1, prominence=0.3)
        for s_idx in sent_troughs:
            val = float(sent_arr[s_idx])
            date_label = dates[s_idx] if s_idx < len(dates) else f"T-{n - s_idx}"
            if val < 0.0:  # Net negative
                sentiment_anomalies.append({
                    "date": date_label,
                    "sentimentScore": round(val, 2),
                    "type": "SENTIMENT_TROUGH_MINIMA",
                    "description": f"Customer sentiment dropped to {val:+.2f} at {date_label}",
                })

    # 4. Momentum Vector
    recent_trend = signal[-1] - signal[-2]
    if recent_trend > 1:
        momentum = "ACCELERATING"
    elif recent_trend < -1:
        momentum = "DECELERATING"
    else:
        momentum = "STABLE"

    # 5. Current State Classification
    is_at_peak = bool(len(peaks) > 0 and peaks[-1] == (n - 1))
    is_at_trough = bool(len(troughs) > 0 and troughs[-1] == (n - 1))

    if is_at_peak:
        current_status = "ACTIVITY_PEAK_MAXIMA"
        summary_desc = f"{competitor_name} is currently experiencing an activity peak (local maximum)."
    elif is_at_trough:
        current_status = "STAGNATION_MINIMA"
        summary_desc = f"{competitor_name} is currently in a quiet trough (local minimum)."
    else:
        current_status = "NORMAL_BASELINE"
        summary_desc = f"{competitor_name} is operating at standard baseline velocity."

    return {
        "maxima": maxima_events,
        "minima": minima_events,
        "sentimentTroughs": sentiment_anomalies,
        "volatility": round(std_val, 2),
        "meanVolume": round(mean_val, 1),
        "momentum": momentum,
        "currentStatus": current_status,
        "summary": summary_desc,
    }
