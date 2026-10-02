"""
Verification unit tests for Phase 2 Live Competitor Monitoring.
"""

import sys
import asyncio
from fastapi.testclient import TestClient

import main
from main import app
from auth import get_current_user
import document_processing_service
from document_processing_service import calculate_impact_score

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
    "weekly_brief": "Competitor activity was moderate this week.",
    "top_threats": [{"threat": "Pricing discount by CompA", "competitor": "CompA", "urgency": "HIGH", "recommendedAction": "Monitor pricing page"}],
    "opportunities": [{"opportunity": "Launch new feature", "basis": "Competitor gap", "recommendedAction": "Accelerate roadmap"}],
    "watch_list": ["CompA"],
    "strategic_recommendations": ["Review product roadmap"],
    "weekly_brief_generated_at": "2026-08-09T12:00:00Z"
}

def mock_get_company_profile(user_id: str):
    return MOCK_COMPANY

main.get_company_profile = mock_get_company_profile
main.get_intelligence_feed = lambda company_id, competitor_id, event_type, impact_label, limit, offset: (
    [
        {
            "id": "doc-1",
            "competitor_id": "comp-1",
            "competitor_name": "CompA",
            "source_url": "https://example.com/news/1",
            "title": "CompA raises $10M Series A",
            "summary": "CompA announced a $10M Series A funding round to expand market share.",
            "event_type": "FUNDING",
            "sentiment": "POSITIVE",
            "sentiment_confidence": 90,
            "relevance_score": 85,
            "relevance_reason": "Competitor funding affects market competition.",
            "impact_score": 88,
            "impact_label": "CRITICAL",
            "published_date": "2026-08-09T00:00:00Z",
            "created_at": "2026-08-09T08:00:00Z",
        }
    ],
    1
)

main.get_intelligence_stats = lambda company_id: {
    "totalDocuments": 1,
    "documentsThisWeek": 1,
    "criticalEvents": 1,
    "highEvents": 0,
    "mediumEvents": 0,
    "lowEvents": 0,
    "byCompetitor": [
        {
            "competitorId": "comp-1",
            "competitorName": "CompA",
            "documentCount": 1,
            "latestEvent": "FUNDING",
            "latestEventDate": "2026-08-09T08:00:00Z"
        }
    ],
    "byEventType": [
        {
            "eventType": "FUNDING",
            "count": 1
        }
    ]
}

main.get_active_monitoring_job = lambda company_id: None
main.create_monitoring_job = lambda company_id, competitor_id, job_type: {"id": "job-123", "status": "RUNNING"}
main.get_monitoring_jobs_history = lambda company_id, limit=20: [
    {
        "id": "job-123",
        "job_type": "NEWS_MONITORING",
        "status": "COMPLETED",
        "documents_found": 5,
        "documents_processed": 3,
        "started_at": "2026-08-09T08:00:00Z",
        "completed_at": "2026-08-09T08:02:00Z",
        "error": None
    }
]

app.dependency_overrides[get_current_user] = lambda: "00000000-0000-0000-0000-000000000001"
client = TestClient(app)

def test_impact_score_formula():
    print("--- Testing Impact Score Formula ---")
    score, label = calculate_impact_score("FUNDING", competitive_score=90, relevance_score=85, sentiment="POSITIVE")
    print(f"FUNDING (comp=90, rel=85, sent=POSITIVE) -> score={score}, label={label}")
    assert score >= 80
    assert label == "CRITICAL"

    score_low, label_low = calculate_impact_score("OTHER", competitive_score=30, relevance_score=20, sentiment="NEUTRAL")
    print(f"OTHER (comp=30, rel=20, sent=NEUTRAL) -> score={score_low}, label={label_low}")
    assert label_low == "LOW"
    print("Impact Score Formula Test PASSED!")


def test_phase2_endpoints():
    print("\n--- 1. GET /api/intelligence/feed ---")
    res = client.get("/api/intelligence/feed")
    assert res.status_code == 200
    feed = res.json()
    print("Feed response:", feed)
    assert feed["total"] == 1
    assert len(feed["documents"]) == 1
    assert feed["documents"][0]["eventType"] == "FUNDING"
    assert feed["documents"][0]["impactLabel"] == "CRITICAL"

    print("\n--- 2. GET /api/intelligence/summary ---")
    res = client.get("/api/intelligence/summary")
    assert res.status_code == 200
    summary = res.json()
    print("Summary response:", summary)
    assert "weeklyBrief" in summary
    assert len(summary["topThreats"]) == 1

    print("\n--- 3. GET /api/intelligence/stats ---")
    res = client.get("/api/intelligence/stats")
    assert res.status_code == 200
    stats = res.json()
    print("Stats response:", stats)
    assert stats["totalDocuments"] == 1
    assert stats["criticalEvents"] == 1

    print("\n--- 4. POST /api/intelligence/trigger-monitoring ---")
    res = client.post("/api/intelligence/trigger-monitoring")
    assert res.status_code == 200
    trigger_res = res.json()
    print("Trigger response:", trigger_res)
    assert trigger_res["message"] == "Monitoring job started"
    assert "jobId" in trigger_res

    print("\n--- 5. GET /api/intelligence/jobs ---")
    res = client.get("/api/intelligence/jobs")
    assert res.status_code == 200
    jobs = res.json()
    print("Jobs response:", jobs)
    assert len(jobs["jobs"]) == 1
    assert jobs["jobs"][0]["status"] == "COMPLETED"

    print("\nALL PHASE 2 LIVE COMPETITOR MONITORING UNIT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_impact_score_formula()
    test_phase2_endpoints()
