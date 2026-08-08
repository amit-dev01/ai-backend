"""
Verification script for Async Competitor Discovery & Intelligence Endpoints.
"""

import sys
import asyncio
from fastapi.testclient import TestClient

import main
from main import app
from auth import get_current_user

MOCK_COMPANY = {
    "id": "11111111-1111-1111-1111-111111111111",
    "owner_id": "00000000-0000-0000-0000-000000000001",
    "company_name": "TestCo",
    "website": "https://testco.com",
    "industry": "Software",
    "description": "Building competitive intelligence software",
    "products_or_services": ["CI Platform"],
    "targetCustomers": "Enterprises",
    "setup_status": "COMPLETED",
    "setup_progress": 100,
    "setup_current_step": "Done"
}

def mock_get_company_profile(user_id: str):
    return MOCK_COMPANY

main.get_company_profile = mock_get_company_profile
main.get_competitors_for_company = lambda company_id: [
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "company_id": company_id,
        "name": "Competitor A",
        "website_url": "https://compa.com",
        "description": "A top competitor",
        "type": "DIRECT",
        "source": "AI_DISCOVERED",
        "competitive_score": 85,
        "confidence_score": 90,
        "product_similarity": 80,
        "customer_overlap": 85,
        "market_overlap": 85,
        "business_model_overlap": 80,
        "reason": "Direct overlap in CI space",
        "is_accepted": None
    }
]
main.save_manual_competitor = lambda company_id, name, website: {
    "id": "33333333-3333-3333-3333-333333333333",
    "company_id": company_id,
    "name": name,
    "website_url": website,
    "source": "MANUAL",
    "is_accepted": True
}
main.get_competitor_by_id = lambda competitor_id: {
    "id": competitor_id,
    "company_id": "11111111-1111-1111-1111-111111111111",
    "name": "Competitor A",
    "is_accepted": None
}
main.update_competitor_accepted = lambda competitor_id, is_accepted: {
    "id": competitor_id,
    "company_id": "11111111-1111-1111-1111-111111111111",
    "name": "Competitor A",
    "is_accepted": is_accepted
}

app.dependency_overrides[get_current_user] = lambda: "00000000-0000-0000-0000-000000000001"
client = TestClient(app)

def test_endpoints():
    print("--- 1. Health check ---")
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    print("Health check PASSED:", res.json())

    print("\n--- 2. GET /api/company/setup-status (before setup) ---")
    res = client.get("/api/company/setup-status")
    assert res.status_code == 200
    data = res.json()
    print("Setup status response:", data)
    assert "status" in data
    assert "progress" in data

    print("\n--- 3. GET /api/competitors ---")
    res = client.get("/api/competitors")
    assert res.status_code == 200
    comp_data = res.json()
    print("Competitors response summary: total =", comp_data.get("total"))
    assert "competitors" in comp_data
    assert "total" in comp_data

    print("\n--- 4. POST /api/competitors/manual ---")
    res = client.post("/api/competitors/manual", json={"name": "TestCompetitor", "website": "https://example.com"})
    assert res.status_code == 200
    manual_res = res.json()
    print("Manual competitor created:", manual_res)
    assert manual_res["name"] == "TestCompetitor"
    assert manual_res["source"] == "MANUAL"

    print("\n--- 5. GET /api/company/profile ---")
    res = client.get("/api/company/profile")
    assert res.status_code == 200
    profile_res = res.json()
    print("Profile response:", profile_res)
    assert "setupCompleted" in profile_res

    print("\nALL API ENDPOINT UNIT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_endpoints()
