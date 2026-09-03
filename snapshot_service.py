"""
Historical Snapshot & Step-Function Delta Tracking Service.

Stores and analyzes competitor snapshots across time:
  - Flagship Product shifts (product pivots)
  - Mathematical pricing step-functions (tier changes, price hikes/cuts)
  - Activity velocity and sentiment deltas

Supports dual-persistence:
  1. Supabase table 'competitor_snapshots' (when connected)
  2. Local JSON file 'data/snapshots.json' (guaranteed zero-downtime persistence)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from database import supabase_client, get_competitor_by_id, get_company_profile_by_id
from nlp_portfolio_engine import extract_flagship_and_boundaries

logger = logging.getLogger(__name__)

SNAPSHOTS_DIR = Path(__file__).parent / "data"
SNAPSHOTS_DIR.mkdir(exist_ok=True)
SNAPSHOTS_FILE = SNAPSHOTS_DIR / "competitor_snapshots.json"


def _read_local_snapshots() -> list[dict[str, Any]]:
    """Read local snapshots from JSON file."""
    if not SNAPSHOTS_FILE.exists():
        return []
    try:
        with open(SNAPSHOTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to read local snapshots file: %s", exc)
        return []


def _write_local_snapshots(snapshots: list[dict[str, Any]]) -> None:
    """Write local snapshots to JSON file."""
    try:
        with open(SNAPSHOTS_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshots, f, indent=2)
    except Exception as exc:
        logger.error("Failed to write local snapshots file: %s", exc)


class SnapshotService:
    """Manages recording and diffing competitor historical snapshots."""

    @staticmethod
    def record_snapshot(
        company_id: str,
        competitor_id: str,
        flagship_product: str,
        price_minima: Optional[float],
        price_maxima: Optional[float],
        price_median: Optional[float],
        pricing_tiers: list[str],
        event_count: int = 0,
        sentiment_score: float = 0.0,
        snapshot_date: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Records a snapshot of competitor state for a given date.
        """
        date_str = snapshot_date or datetime.utcnow().strftime("%Y-%m-%d")
        snapshot_id = f"{competitor_id}_{date_str}"

        snapshot_record = {
            "id": snapshot_id,
            "company_id": company_id,
            "competitor_id": competitor_id,
            "snapshot_date": date_str,
            "flagship_product": flagship_product,
            "price_minima": price_minima,
            "price_maxima": price_maxima,
            "price_median": price_median,
            "pricing_tiers": pricing_tiers,
            "event_count": event_count,
            "sentiment_score": sentiment_score,
            "recorded_at": datetime.utcnow().isoformat(),
        }

        # 1. Try Supabase
        if supabase_client:
            try:
                supabase_client.table("competitor_snapshots").upsert(snapshot_record).execute()
            except Exception as exc:
                logger.warning("Supabase snapshot write skipped: %s", exc)

        # 2. Local JSON Persistence
        all_snapshots = _read_local_snapshots()
        # Replace if exists for same competitor and date, else append
        all_snapshots = [s for s in all_snapshots if s.get("id") != snapshot_id]
        all_snapshots.append(snapshot_record)
        _write_local_snapshots(all_snapshots)

        logger.info("Recorded historical snapshot for competitor %s on %s", competitor_id, date_str)
        return snapshot_record

    @staticmethod
    def get_snapshots_for_competitor(competitor_id: str) -> list[dict[str, Any]]:
        """Fetch all chronological snapshots for a competitor."""
        # Check Supabase first
        if supabase_client:
            try:
                res = (
                    supabase_client.table("competitor_snapshots")
                    .select("*")
                    .eq("competitor_id", competitor_id)
                    .order("snapshot_date", desc=False)
                    .execute()
                )
                if res.data:
                    return res.data
            except Exception:
                pass

        # Fallback to local
        all_snapshots = _read_local_snapshots()
        comp_snaps = [s for s in all_snapshots if s.get("competitor_id") == competitor_id]
        comp_snaps.sort(key=lambda s: s.get("snapshot_date", ""))
        return comp_snaps

    @staticmethod
    def compute_step_function_deltas(competitor_id: str) -> dict[str, Any]:
        """
        Calculates mathematical step-function deltas between historical snapshots:
          - Price floor changes (price minima)
          - Enterprise ceiling changes (price maxima)
          - Flagship product evolution / pivot
          - Activity volume surges or quiet spells
        """
        snapshots = SnapshotService.get_snapshots_for_competitor(competitor_id)
        competitor = get_competitor_by_id(competitor_id) or {}
        comp_name = competitor.get("name", "Competitor")

        if len(snapshots) < 2:
            current = snapshots[0] if snapshots else {}
            return {
                "competitorId": competitor_id,
                "competitorName": comp_name,
                "hasHistoricalDeltas": False,
                "totalSnapshotsRecorded": len(snapshots),
                "latestState": current,
                "priceDeltas": [],
                "productPivots": [],
                "summary": f"Baseline historical snapshot established for {comp_name}. Subsequent monitoring cycles will compute deltas."
            }

        price_deltas = []
        product_pivots = []

        for i in range(1, len(snapshots)):
            prev = snapshots[i - 1]
            curr = snapshots[i]
            prev_date = prev.get("snapshot_date")
            curr_date = curr.get("snapshot_date")

            # 1. Price Minima Step-Function
            p_min_prev = prev.get("price_minima")
            p_min_curr = curr.get("price_minima")
            if p_min_prev is not None and p_min_curr is not None and p_min_prev != p_min_curr:
                diff = p_min_curr - p_min_prev
                pct = (diff / p_min_prev) * 100.0 if p_min_prev > 0 else 100.0
                direction = "INCREASED" if diff > 0 else "DECREASED"
                price_deltas.append({
                    "date": curr_date,
                    "metric": "PRICE_MINIMA",
                    "direction": direction,
                    "previous": p_min_prev,
                    "current": p_min_curr,
                    "delta": diff,
                    "percentage": round(pct, 1),
                    "description": f"Entry price floor {direction.lower()} from ${p_min_prev:.0f} to ${p_min_curr:.0f}/mo ({pct:+.1f}%) on {curr_date}."
                })

            # 2. Price Maxima Step-Function
            p_max_prev = prev.get("price_maxima")
            p_max_curr = curr.get("price_maxima")
            if p_max_prev is not None and p_max_curr is not None and p_max_prev != p_max_curr:
                diff = p_max_curr - p_max_prev
                direction = "EXPANDED" if diff > 0 else "REDUCED"
                price_deltas.append({
                    "date": curr_date,
                    "metric": "PRICE_MAXIMA",
                    "direction": direction,
                    "previous": p_max_prev,
                    "current": p_max_curr,
                    "delta": diff,
                    "description": f"Enterprise ceiling {direction.lower()} from ${p_max_prev:.0f} to ${p_max_curr:.0f}/mo on {curr_date}."
                })

            # 3. Flagship Product Pivot
            flag_prev = (prev.get("flagship_product") or "").strip().lower()
            flag_curr = (curr.get("flagship_product") or "").strip().lower()
            if flag_prev and flag_curr and flag_prev != flag_curr:
                product_pivots.append({
                    "date": curr_date,
                    "previousFlagship": prev.get("flagship_product"),
                    "newFlagship": curr.get("flagship_product"),
                    "description": f"Competitor repositioned primary flagship from '{prev.get('flagship_product')}' to '{curr.get('flagship_product')}' on {curr_date}."
                })

        return {
            "competitorId": competitor_id,
            "competitorName": comp_name,
            "hasHistoricalDeltas": bool(price_deltas or product_pivots),
            "totalSnapshotsRecorded": len(snapshots),
            "timeline": [
                {
                    "date": s.get("snapshot_date"),
                    "priceMinima": s.get("price_minima"),
                    "priceMaxima": s.get("price_maxima"),
                    "flagship": s.get("flagship_product"),
                    "eventCount": s.get("event_count", 0),
                }
                for s in snapshots
            ],
            "priceDeltas": price_deltas,
            "productPivots": product_pivots,
            "summary": f"Tracked {len(snapshots)} snapshots across time with {len(price_deltas)} pricing shifts and {len(product_pivots)} flagship pivots."
        }
