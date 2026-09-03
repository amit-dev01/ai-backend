"""
Competitive 2D Positioning Radar & Encroachment Engine.

Projects our company and all active competitors onto a normalized 2D spatial coordinate system:
  - X-Axis: Market Tier & Price Boundary [0.0 = Freemium/SMB to 100.0 = Enterprise]
  - Y-Axis: Product Scope & Breadth [0.0 = Specialized Point Solution to 100.0 = All-in-One Platform]

Calculates:
  1. Competitor Coordinates (x, y)
  2. Euclidean Proximity & Threat Encroachment (distance to our company)
  3. Market Quadrant Classification (Leaders, Specialists, Challengers, Point Solutions)
  4. White Space Opportunity Zones (optimal coordinates with maximum distance from competitors)
"""

import logging
import math
from typing import Any, Optional
import numpy as np

from database import get_competitors_for_company, get_company_profile_by_id
from nlp_portfolio_engine import extract_flagship_and_boundaries
from snapshot_service import SnapshotService

logger = logging.getLogger(__name__)


def _calculate_x_coordinate(price_minima: Optional[float], price_maxima: Optional[float], target_customers: str) -> float:
    """
    Computes X-coordinate [0.0 to 100.0] representing market tier from budget/SMB to high enterprise.
    """
    x_score = 30.0  # default mid-market baseline
    cust_lower = (target_customers or "").lower()

    if "enterprise" in cust_lower or "fortune" in cust_lower or "large" in cust_lower:
        x_score += 35.0
    elif "startup" in cust_lower or "smb" in cust_lower or "freelance" in cust_lower:
        x_score -= 15.0

    if price_maxima is not None:
        if price_maxima >= 500.0:
            x_score += 30.0
        elif price_maxima >= 200.0:
            x_score += 15.0
        elif price_maxima <= 50.0:
            x_score -= 15.0

    if price_minima is not None and price_minima == 0.0:
        x_score -= 10.0

    return max(5.0, min(95.0, round(x_score, 1)))


def _calculate_y_coordinate(flagship_name: str, description: str, notes: str) -> float:
    """
    Computes Y-coordinate [0.0 to 100.0] representing product breadth:
    Point Solution (0.0) -> Multi-Product Platform -> All-in-One Operating System (100.0).
    """
    y_score = 45.0  # default balanced baseline
    combined_text = f"{flagship_name} {description} {notes}".lower()

    platform_keywords = ["platform", "suite", "all-in-one", "ecosystem", "cloud", "operating system", "end-to-end", "unified"]
    specialist_keywords = ["extension", "plugin", "api", "widget", "single", "focused", "lightweight", "micro", "standalone"]

    platform_hits = sum(1 for kw in platform_keywords if kw in combined_text)
    specialist_hits = sum(1 for kw in specialist_keywords if kw in combined_text)

    y_score += (platform_hits * 10.0)
    y_score -= (specialist_hits * 12.0)

    # Word count heuristic: more extensive descriptions typically indicate broader feature sets
    desc_words = len(description.split())
    if desc_words > 40:
        y_score += 10.0
    elif desc_words < 15:
        y_score -= 10.0

    return max(5.0, min(95.0, round(y_score, 1)))


def _classify_quadrant(x: float, y: float) -> str:
    """Assigns category quadrant based on (x, y) coordinates."""
    if x >= 50.0 and y >= 50.0:
        return "ENTERPRISE_PLATFORM"  # Leaders / High Price, High Breadth
    elif x >= 50.0 and y < 50.0:
        return "PREMIUM_SPECIALIST"   # High Price, Highly Focused
    elif x < 50.0 and y >= 50.0:
        return "DISRUPTIVE_CHALLENGER" # Low/Mid Price, High Breadth (Volume Play)
    else:
        return "LIGHTWEIGHT_POINT_SOLUTION" # Low Price, Focused Point Tool


class PositioningEngine:
    """Generates 2D competitive spatial radar and whitespace opportunities."""

    @staticmethod
    def get_positioning_radar(company_id: str) -> dict[str, Any]:
        """
        Computes 2D spatial positioning coordinates for our company and all competitors.
        """
        company = get_company_profile_by_id(company_id) or {}
        our_name = company.get("company_name", "Our Company")
        our_desc = company.get("description", "")
        our_products = company.get("products_or_services", [])
        our_products_str = ", ".join(our_products) if isinstance(our_products, list) else str(our_products)
        our_customers = company.get("target_customers", "")

        # 1. Compute Our Company's (x, y)
        our_x = _calculate_x_coordinate(price_minima=29.0, price_maxima=299.0, target_customers=our_customers)
        our_y = _calculate_y_coordinate(flagship_name=our_products_str, description=our_desc, notes="")
        our_quadrant = _classify_quadrant(our_x, our_y)

        our_node = {
            "id": "our_company",
            "name": our_name,
            "isHomeTeam": True,
            "x": our_x,
            "y": our_y,
            "quadrant": our_quadrant,
            "flagship": our_products_str[:40] or "Core Offering",
            "marketFocus": "Enterprise & Growth" if our_x >= 50 else "SMB & Fast-Movers",
            "productScope": "Unified Platform" if our_y >= 50 else "Specialized Solution",
        }

        # 2. Compute Competitor Nodes
        competitors = get_competitors_for_company(company_id, status="active", accepted="true")
        if not competitors:
            competitors = get_competitors_for_company(company_id, status="active")

        competitor_nodes = []
        occupied_coords = [(our_x, our_y)]

        for comp in competitors:
            comp_id = str(comp.get("id"))
            comp_name = comp.get("name", "Competitor")
            comp_desc = comp.get("description", "")
            comp_notes = comp.get("notes", "")
            comp_score = comp.get("competitive_score", 50)

            # Check snapshot first
            snapshots = SnapshotService.get_snapshots_for_competitor(comp_id)
            if snapshots:
                latest = snapshots[-1]
                flagship = latest.get("flagship_product", comp_name)
                p_min = latest.get("price_minima")
                p_max = latest.get("price_maxima")
            else:
                nlp_res = extract_flagship_and_boundaries(
                    content=f"{comp_desc}\n{comp_notes}",
                    headers_text=comp_name,
                    competitor_name=comp_name
                )
                flagship = nlp_res.get("flagshipProduct", comp_name)
                p_min = nlp_res.get("priceMinima")
                p_max = nlp_res.get("priceMaxima")

            cx = _calculate_x_coordinate(price_minima=p_min, price_maxima=p_max, target_customers=comp_desc)
            cy = _calculate_y_coordinate(flagship_name=flagship, description=comp_desc, notes=comp_notes)
            c_quadrant = _classify_quadrant(cx, cy)

            # Euclidean distance to our company
            dist_to_us = math.sqrt((our_x - cx) ** 2 + (our_y - cy) ** 2)
            threat_level = "CRITICAL_ENCROACHMENT" if dist_to_us < 20.0 else ("HIGH_OVERLAP" if dist_to_us < 40.0 else "MODERATE")

            competitor_nodes.append({
                "id": comp_id,
                "name": comp_name,
                "isHomeTeam": False,
                "x": cx,
                "y": cy,
                "quadrant": c_quadrant,
                "flagship": flagship,
                "distanceToUs": round(dist_to_us, 1),
                "threatLevel": threat_level,
                "competitiveScore": comp_score,
                "website": comp.get("website_url"),
            })
            occupied_coords.append((cx, cy))

        # Sort competitors by spatial proximity (closest = highest encroachment risk)
        competitor_nodes.sort(key=lambda n: n["distanceToUs"])

        # 3. Compute Uncontested White Space Coordinates
        # Sample test points across the 4 quadrant zones and find candidate with maximum distance to existing players
        candidate_test_points = [
            (25.0, 75.0, "DISRUPTIVE_CHALLENGER", "High-capability platform at an accessible price point"),
            (75.0, 25.0, "PREMIUM_SPECIALIST", "High-ticket, deeply specialized expert point solution"),
            (20.0, 25.0, "LIGHTWEIGHT_ENTRY", "Frictionless micro-solution with instant adoption"),
            (80.0, 80.0, "ENTERPRISE_GIANT", "Full-scale governance and compliance enterprise suite"),
        ]

        whitespace_recommendations = []
        for tx, ty, quad_name, rationale in candidate_test_points:
            min_dist_to_any_competitor = min(math.sqrt((tx - ox) ** 2 + (ty - oy) ** 2) for ox, oy in occupied_coords)
            if min_dist_to_any_competitor >= 25.0:  # Significant gap
                whitespace_recommendations.append({
                    "targetX": tx,
                    "targetY": ty,
                    "quadrant": quad_name,
                    "clearanceDistance": round(min_dist_to_any_competitor, 1),
                    "strategicRationale": rationale,
                    "opportunityStatus": "OPEN_WHITE_SPACE"
                })

        whitespace_recommendations.sort(key=lambda w: w["clearanceDistance"], reverse=True)

        return {
            "companyId": company_id,
            "totalEntitiesMapped": len(competitor_nodes) + 1,
            "axes": {
                "xAxis": {"label": "Market Focus & Price Tier", "min": "SMB / Freemium", "max": "High-End Enterprise"},
                "yAxis": {"label": "Product Architecture Scope", "min": "Specialized Point Tool", "max": "Unified All-in-One Platform"},
            },
            "homeTeam": our_node,
            "competitors": competitor_nodes,
            "whiteSpaceOpportunities": whitespace_recommendations[:2],
            "strategicPositioningSummary": (
                f"{our_name} sits in the '{our_quadrant}' quadrant. "
                f"Your closest market encroacher is '{competitor_nodes[0]['name'] if competitor_nodes else 'None'}' "
                f"(spatial distance: {competitor_nodes[0]['distanceToUs'] if competitor_nodes else 'N/A'})."
            )
        }
