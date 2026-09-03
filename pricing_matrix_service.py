"""
Competitive Pricing Matrix Service.

Constructs an interactive category-wide pricing and portfolio matrix:
  - Side-by-side price tiers across all active competitors
  - Category Price Minima (Lowest Market Floor)
  - Category Price Maxima (Highest Enterprise Ceiling)
  - Category Median
  - Uncontested Whitespace Gaps
  - Strategic Pricing Recommendations for Our Company
"""

import logging
from typing import Any, Optional
import numpy as np

from database import get_competitors_for_company, get_company_profile_by_id, supabase_client
from nlp_portfolio_engine import extract_flagship_and_boundaries
from snapshot_service import SnapshotService

logger = logging.getLogger(__name__)


class PricingMatrixService:
    """Constructs live competitive pricing grids and whitespace maps."""

    @staticmethod
    def get_category_pricing_matrix(company_id: str) -> dict[str, Any]:
        """
        Gathers and aggregates pricing boundaries and flagship offerings
        across all active accepted competitors for the company.
        """
        company = get_company_profile_by_id(company_id) or {}
        our_name = company.get("company_name", "Our Company")
        our_industry = company.get("industry", "SaaS")

        competitors = get_competitors_for_company(company_id, status="active", accepted="true")
        if not competitors:
            # Also check without accepted filter if pending
            competitors = get_competitors_for_company(company_id, status="active")

        matrix_rows = []
        all_minimas: list[float] = []
        all_maximas: list[float] = []
        all_medians: list[float] = []

        for comp in competitors:
            comp_id = str(comp.get("id"))
            comp_name = comp.get("name", "Competitor")
            comp_url = comp.get("website_url", "")
            comp_desc = comp.get("description", "")
            comp_notes = comp.get("notes", "")

            # 1. Check historical snapshot first
            snapshots = SnapshotService.get_snapshots_for_competitor(comp_id)
            if snapshots:
                latest = snapshots[-1]
                flagship = latest.get("flagship_product", comp_name)
                p_min = latest.get("price_minima")
                p_max = latest.get("price_maxima")
                p_med = latest.get("price_median")
                tiers = latest.get("pricing_tiers") or []
                whitespace = None
            else:
                # 2. Compute via NLP engine
                text_corpus = f"{comp_desc}\n{comp_notes}"
                nlp_res = extract_flagship_and_boundaries(
                    content=text_corpus,
                    headers_text=comp_name,
                    competitor_name=comp_name
                )
                flagship = nlp_res.get("flagshipProduct", comp_name)
                p_min = nlp_res.get("priceMinima")
                p_max = nlp_res.get("priceMaxima")
                p_med = nlp_res.get("priceMedian")
                tiers = nlp_res.get("pricingTiersFound") or []
                whitespace = nlp_res.get("whiteSpaceOpportunity")

                # Record snapshot for future delta tracking
                SnapshotService.record_snapshot(
                    company_id=company_id,
                    competitor_id=comp_id,
                    flagship_product=flagship,
                    price_minima=p_min,
                    price_maxima=p_max,
                    price_median=p_med,
                    pricing_tiers=tiers,
                )

            if p_min is not None:
                all_minimas.append(p_min)
            if p_max is not None:
                all_maximas.append(p_max)
            if p_med is not None:
                all_medians.append(p_med)

            matrix_rows.append({
                "competitorId": comp_id,
                "name": comp_name,
                "website": comp_url,
                "flagshipProduct": flagship,
                "priceMinima": p_min,
                "priceMaxima": p_max,
                "priceMedian": p_med,
                "tiers": tiers,
                "whitespace": whitespace,
                "positioningTier": (
                    "ENTERPRISE_PREMIUM" if (p_max and p_max > 300)
                    else ("MID_MARKET" if (p_min and p_min >= 49) else "ENTRY_SMB")
                )
            })

        # Category Benchmarks
        cat_floor = float(np.min(all_minimas)) if all_minimas else None
        cat_ceiling = float(np.max(all_maximas)) if all_maximas else None
        cat_median = float(np.median(all_medians)) if all_medians else (
            float(np.median(all_minimas)) if all_minimas else None
        )

        # Detect Macro Whitespace across all players
        combined_tiers = sorted(list(set(all_minimas + all_maximas)))
        category_whitespace = []
        for i in range(len(combined_tiers) - 1):
            gap = combined_tiers[i+1] - combined_tiers[i]
            if gap >= 50.0:
                category_whitespace.append({
                    "fromPrice": combined_tiers[i],
                    "toPrice": combined_tiers[i+1],
                    "gapSize": gap,
                    "description": f"Unoccupied market gap between ${combined_tiers[i]:.0f} and ${combined_tiers[i+1]:.0f}/mo."
                })

        # Strategic Pricing Recommendation
        if cat_median:
            rec_entry = max(19.0, round(cat_median * 0.6, -1))
            rec_pro = round(cat_median * 1.1, -1)
            strategic_recommendation = (
                f"Position entry tier at ${rec_entry:.0f}/mo to undercut the category median (${cat_median:.0f}/mo), "
                f"and capture pro users at ${rec_pro:.0f}/mo with higher feature value."
            )
        else:
            strategic_recommendation = "Establish a clear 3-tier pricing model (Starter, Professional, Enterprise) to anchor market value."

        return {
            "companyId": company_id,
            "companyName": our_name,
            "industry": our_industry,
            "totalCompetitorsAnalyzed": len(matrix_rows),
            "categoryBenchmarks": {
                "marketFloorMinima": cat_floor,
                "marketCeilingMaxima": cat_ceiling,
                "categoryMedian": cat_median,
            },
            "unoccupiedWhitespaceGaps": category_whitespace,
            "strategicRecommendation": strategic_recommendation,
            "competitorMatrix": matrix_rows
        }
