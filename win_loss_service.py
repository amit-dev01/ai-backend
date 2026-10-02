"""
Win/Loss Deal Intelligence Service.

Tracks sales cycle deal outcomes against competitors:
  - Deal Outcomes (WON, LOST, TIED)
  - Head-to-Head Win Rates per competitor
  - Root Cause Analysis (Price, Missing Features, Brand, Implementation)
  - Pipeline Revenue at Risk per competitor
  - Actionable product roadmap & pricing countermeasures
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from database import supabase_client, get_competitor_by_id

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DEALS_FILE = DATA_DIR / "deal_outcomes.json"


def _read_local_deals() -> list[dict[str, Any]]:
    """Read local deals from JSON file."""
    if not DEALS_FILE.exists():
        return []
    try:
        with open(DEALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to read deals file: %s", exc)
        return []


def _write_local_deals(deals: list[dict[str, Any]]) -> None:
    """Write deals to JSON file."""
    try:
        with open(DEALS_FILE, "w", encoding="utf-8") as f:
            json.dump(deals, f, indent=2)
    except Exception as exc:
        logger.error("Failed to write deals file: %s", exc)


class WinLossService:
    """Records deal outcomes and computes competitive win/loss metrics."""

    @staticmethod
    def record_deal_outcome(
        company_id: str,
        competitor_id: str,
        outcome: str,  # WON, LOST, TIED
        deal_value: float = 0.0,
        primary_reason: str = "FEATURE_GAP",  # PRICING, FEATURE_GAP, BRAND_TRUST, USABILITY, SPEED
        competitor_strength: Optional[str] = None,
        notes: Optional[str] = None,
        prospect_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Records a commercial deal outcome against a specific competitor.
        """
        outcome_clean = outcome.upper().strip()
        if outcome_clean not in ("WON", "LOST", "TIED"):
            outcome_clean = "LOST"

        competitor = get_competitor_by_id(competitor_id) or {}
        comp_name = competitor.get("name", "Competitor")

        record = {
            "id": f"deal_{int(datetime.utcnow().timestamp() * 1000)}",
            "company_id": company_id,
            "competitor_id": competitor_id,
            "competitor_name": comp_name,
            "outcome": outcome_clean,
            "deal_value": float(deal_value),
            "primary_reason": primary_reason.upper().strip(),
            "competitor_strength": competitor_strength or "Not specified",
            "prospect_name": prospect_name or "Enterprise Prospect",
            "notes": notes or "",
            "recorded_at": datetime.utcnow().isoformat(),
        }

        # 1. Supabase write
        if supabase_client:
            try:
                supabase_client.table("deal_outcomes").insert(record).execute()
            except Exception as exc:
                logger.warning("Supabase deal write skipped: %s", exc)

        # 2. Local JSON write
        deals = _read_local_deals()
        deals.append(record)
        _write_local_deals(deals)

        logger.info("Recorded %s deal against %s ($%.0f)", outcome_clean, comp_name, deal_value)
        return record

    @staticmethod
    def get_deal_analytics(company_id: str) -> dict[str, Any]:
        """
        Aggregates win rates, root-cause loss reasons, and revenue at risk across all competitors.
        """
        deals = _read_local_deals()
        company_deals = [d for d in deals if d.get("company_id") == company_id]

        total_deals = len(company_deals)
        if total_deals == 0:
            return {
                "totalDealsLogged": 0,
                "overallWinRate": 0.0,
                "wonDeals": 0,
                "lostDeals": 0,
                "tiedDeals": 0,
                "pipelineWon": 0.0,
                "pipelineLost": 0.0,
                "headToHead": [],
                "topLossReasons": [],
                "recommendation": "Log live deal outcomes (WON/LOST) to identify your biggest sales friction points against specific competitors."
            }

        won_deals = [d for d in company_deals if d.get("outcome") == "WON"]
        lost_deals = [d for d in company_deals if d.get("outcome") == "LOST"]
        tied_deals = [d for d in company_deals if d.get("outcome") == "TIED"]

        win_rate = round((len(won_deals) / total_deals) * 100.0, 1)
        pipeline_won = sum(d.get("deal_value", 0.0) for d in won_deals)
        pipeline_lost = sum(d.get("deal_value", 0.0) for d in lost_deals)

        # Head to Head breakdown per competitor
        comp_map: dict[str, list[dict]] = {}
        for d in company_deals:
            cid = d.get("competitor_id", "unknown")
            comp_map.setdefault(cid, []).append(d)

        head_to_head = []
        for cid, cdeals in comp_map.items():
            c_name = cdeals[0].get("competitor_name", "Competitor")
            c_won = len([d for d in cdeals if d.get("outcome") == "WON"])
            c_lost = len([d for d in cdeals if d.get("outcome") == "LOST"])
            c_total = len(cdeals)
            c_win_rate = round((c_won / c_total) * 100.0, 1) if c_total > 0 else 0.0
            c_lost_val = sum(d.get("deal_value", 0.0) for d in cdeals if d.get("outcome") == "LOST")

            head_to_head.append({
                "competitorId": cid,
                "competitorName": c_name,
                "totalEngagements": c_total,
                "winRate": c_win_rate,
                "won": c_won,
                "lost": c_lost,
                "revenueLost": c_lost_val,
                "dangerRank": "CRITICAL" if (c_win_rate < 40.0 and c_lost >= 2) else "MODERATE"
            })

        head_to_head.sort(key=lambda h: h["revenueLost"], reverse=True)

        # Loss Reasons Breakdown
        reason_map: dict[str, int] = {}
        for d in lost_deals:
            r = d.get("primary_reason", "OTHER")
            reason_map[r] = reason_map.get(r, 0) + 1

        top_loss_reasons = [
            {"reason": r, "count": count, "percentage": round((count / len(lost_deals)) * 100.0, 1)}
            for r, count in sorted(reason_map.items(), key=lambda x: x[1], reverse=True)
        ]

        # Strategic Recommendation
        primary_loss = top_loss_reasons[0]["reason"] if top_loss_reasons else "NONE"
        toughest_adversary = head_to_head[0]["competitorName"] if head_to_head else "Competitors"

        if primary_loss == "PRICING":
            rec = f"Primary loss driver is PRICING against {toughest_adversary}. Introduce a competitive entry tier or emphasize TCO in sales battlecards."
        elif primary_loss == "FEATURE_GAP":
            rec = f"Primary loss driver is FEATURE_GAP against {toughest_adversary}. Align product roadmap with specific customer objections."
        else:
            rec = f"Focus sales enablement on counter-positioning against {toughest_adversary} to increase win rates."

        return {
            "totalDealsLogged": total_deals,
            "overallWinRate": win_rate,
            "wonDeals": len(won_deals),
            "lostDeals": len(lost_deals),
            "tiedDeals": len(tied_deals),
            "pipelineWon": pipeline_won,
            "pipelineLost": pipeline_lost,
            "headToHead": head_to_head,
            "topLossReasons": top_loss_reasons,
            "strategicRecommendation": rec
        }
