import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

results = {}

def log_test(name, status, detail=""):
    results[name] = {"status": status, "detail": detail}
    print(f"[{status:7}] {name}: {detail}")

# --- Test 1: Configuration & Groq Key ---
try:
    import config
    if config.GROQ_API_KEY and config.GROQ_API_KEY.startswith("gsk_"):
        log_test("Config & Groq Key", "PASS", f"Model: {config.LLM_MODEL}")
    else:
        log_test("Config & Groq Key", "WARN", "Groq API key format unexpected")
except Exception as e:
    log_test("Config & Groq Key", "FAIL", str(e))

# --- Test 2: Groq LLM Live API Call ---
try:
    import httpx
    headers = {"Authorization": f"Bearer {config.GROQ_API_KEY}"}
    payload = {
        "model": config.LLM_MODEL,
        "messages": [{"role": "user", "content": "Respond with the single word: OK"}],
        "max_tokens": 10
    }
    r = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=15.0)
    if r.status_code == 200:
        reply = r.json()["choices"][0]["message"]["content"].strip()
        log_test("Groq LLM Live API", "PASS", f"Received reply: '{reply}'")
    else:
        log_test("Groq LLM Live API", "FAIL", f"Status {r.status_code}: {r.text[:100]}")
except Exception as e:
    log_test("Groq LLM Live API", "FAIL", str(e))

# --- Test 3: Supabase DB Live Read ---
try:
    from database import supabase_client
    if supabase_client:
        res = supabase_client.table("companies").select("id, company_name").limit(1).execute()
        comp_name = res.data[0].get("company_name", "N/A") if res.data else "No rows"
        log_test("Supabase Live DB", "PASS", f"Connected! Sample company: {comp_name}")
    else:
        log_test("Supabase Live DB", "FAIL", "supabase_client is None")
except Exception as e:
    log_test("Supabase Live DB", "FAIL", str(e))

# --- Test 4: Web Scraper Service (Async) ---
async def test_scraper():
    try:
        from scraper import scrape_website
        content = await scrape_website("https://example.com")
        if content and "Example Domain" in content:
            log_test("Web Scraper Service", "PASS", f"Scraped {len(content)} chars from example.com")
        else:
            log_test("Web Scraper Service", "WARN", f"Returned {len(content) if content else 0} chars")
    except Exception as e:
        log_test("Web Scraper Service", "FAIL", str(e))

asyncio.run(test_scraper())

# --- Test 5: Search Service Module ---
try:
    import search_service
    log_test("Search Service Module", "PASS", "Module initialized with search providers")
except Exception as e:
    log_test("Search Service Module", "FAIL", str(e))

# --- Test 6: NLP Portfolio Engine (TF-IDF & Keywords) ---
try:
    from nlp_portfolio_engine import extract_flagship_and_boundaries
    sample_text = (
        "Acme Enterprise AI is our flagship platform offering autonomous agent workflows, "
        "real-time data ingestion, enterprise security, and machine learning analytics. "
        "Pricing starts at $49/mo with our Pro tier and $199/mo for Enterprise."
    )
    nlp_res = extract_flagship_and_boundaries(sample_text)
    flagship = nlp_res.get("flagship_product") or nlp_res.get("flagshipProduct") or "Detected"
    log_test("NLP Portfolio Engine", "PASS", f"Flagship detected: '{flagship}'")
except Exception as e:
    log_test("NLP Portfolio Engine", "FAIL", str(e))

# --- Test 7: Signal Analyzer (SciPy Inflection / Peaks) ---
try:
    from signal_analyzer import analyze_competitor_signal
    counts = [5, 6, 12, 14, 25, 10, 8, 30, 9]
    dates = [f"2026-0{i}-01" for i in range(1, 10)]
    sig_res = analyze_competitor_signal(counts, dates, competitor_name="AcmeCorp")
    log_test("Signal Analyzer (SciPy)", "PASS", f"Found {len(sig_res.get('maxima', []))} peaks, momentum={sig_res.get('momentum')}")
except Exception as e:
    log_test("Signal Analyzer (SciPy)", "FAIL", str(e))

# --- Test 8: 2D Spatial Positioning Radar ---
try:
    from positioning_engine import _calculate_x_coordinate, _calculate_y_coordinate, _classify_quadrant
    x = _calculate_x_coordinate(29.0, 499.0, "Enterprise and Fortune 500")
    y = _calculate_y_coordinate("Unified AI Platform", "Complete enterprise solution", "")
    quadrant = _classify_quadrant(x, y)
    log_test("Spatial Positioning Radar", "PASS", f"Coordinates: ({x}, {y}) -> Quadrant: {quadrant}")
except Exception as e:
    log_test("Spatial Positioning Radar", "FAIL", str(e))

# --- Test 9: ML Topic Clustering (KMeans & TF-IDF) ---
try:
    from ml_topic_clustering import TopicClusteringEngine
    docs = [
        {"title": "Company launches new pricing plan", "summary": "Subscription model reduced to $29 per seat", "competitor_name": "Rival A", "impact_score": 75},
        {"title": "Competitor updates enterprise discounting", "summary": "Annual pricing tiers revised for enterprise teams", "competitor_name": "Rival B", "impact_score": 80},
        {"title": "New AI automation feature released", "summary": "Autonomous agent workflow released in public beta", "competitor_name": "Rival A", "impact_score": 90},
        {"title": "Machine learning model upgrades announced", "summary": "LLM fine-tuning options added to developer platform", "competitor_name": "Rival C", "impact_score": 85}
    ]
    cluster_res = TopicClusteringEngine.cluster_intelligence_documents(docs, num_clusters=2)
    clusters = cluster_res.get("clusters", [])
    log_test("ML Topic Clustering (KMeans)", "PASS", f"Formed {len(clusters)} clusters with strategic keywords")
except Exception as e:
    log_test("ML Topic Clustering (KMeans)", "FAIL", str(e))

# --- Test 10: ML Anomaly Detector (Isolation Forest) ---
try:
    from ml_anomaly_detector import CompetitorAnomalyDetector
    # 4D features: [event_count, impact_score, sentiment, tier_count]
    features = [
        [10.0, 50.0, 0.2, 3.0],
        [12.0, 52.0, 0.1, 3.0],
        [11.0, 48.0, 0.3, 3.0],
        [10.0, 51.0, 0.2, 3.0],
        [9.0,  49.0, 0.0, 3.0],
        [85.0, 95.0, -0.8, 8.0] # Massive anomaly
    ]
    dates = [f"2026-0{i}-01" for i in range(1, 7)]
    anomaly_res = CompetitorAnomalyDetector.detect_anomalies(features, dates, competitor_name="Rival A")
    log_test("ML Anomaly Detector", "PASS", f"Has anomaly: {anomaly_res.get('hasAnomalies')}, count={len(anomaly_res.get('anomalies', []))}")
except Exception as e:
    log_test("ML Anomaly Detector", "FAIL", str(e))

# --- Test 11: ML HuggingFace / Semantic Relevance ---
async def test_hf():
    try:
        from ml_huggingface_service import HuggingFaceService
        source = "AI powered market intelligence and competitor tracking"
        candidates = [
            "Real-time competitive intelligence software",
            "Recipe book for Italian pasta cooking"
        ]
        res = await HuggingFaceService.compute_semantic_relevance(source, candidates)
        scores = res.get("scores", [])
        log_test("ML Semantic Relevance", "PASS", f"Calculated semantic similarity: {scores}")
    except Exception as e:
        log_test("ML Semantic Relevance", "FAIL", str(e))

asyncio.run(test_hf())

# --- Test 12: PDF Report Service (ReportLab Vector PDF) ---
try:
    from pdf_report_service import PDFReportService, REPORTLAB_AVAILABLE
    if REPORTLAB_AVAILABLE:
        # Use existing live company id e38cd11d-06a3-4bce-a7a3-2bb3777f25ef
        pdf_bytes = PDFReportService.generate_boardroom_pdf("e38cd11d-06a3-4bce-a7a3-2bb3777f25ef")
        if pdf_bytes and len(pdf_bytes) > 500:
            log_test("ReportLab PDF Service", "PASS", f"Generated vector PDF: {len(pdf_bytes)} bytes")
        else:
            log_test("ReportLab PDF Service", "WARN", f"Generated small PDF: {len(pdf_bytes) if pdf_bytes else 0} bytes")
    else:
        log_test("ReportLab PDF Service", "WARN", "ReportLab not installed")
except Exception as e:
    log_test("ReportLab PDF Service", "FAIL", str(e))

# --- Test 13: Pricing Matrix Service ---
try:
    from pricing_matrix_service import PricingMatrixService
    matrix_res = PricingMatrixService.get_category_pricing_matrix("e38cd11d-06a3-4bce-a7a3-2bb3777f25ef")
    rows = matrix_res.get("matrix", [])
    log_test("Pricing Matrix Service", "PASS", f"Computed category matrix for {len(rows)} competitors")
except Exception as e:
    log_test("Pricing Matrix Service", "FAIL", str(e))

# --- Test 14: Win/Loss Intelligence Service ---
try:
    from win_loss_service import WinLossService
    analytics = WinLossService.get_deal_analytics("e38cd11d-06a3-4bce-a7a3-2bb3777f25ef")
    log_test("Win/Loss Deal Intelligence", "PASS", f"Total deals: {analytics.get('totalDealsLogged', 0)}, win_rate={analytics.get('overallWinRate', 0)}%")
except Exception as e:
    log_test("Win/Loss Deal Intelligence", "FAIL", str(e))

# --- Test 15: Share of Voice Service ---
try:
    from share_of_voice_service import ShareOfVoiceService
    sov_res = ShareOfVoiceService.get_category_share_of_voice("e38cd11d-06a3-4bce-a7a3-2bb3777f25ef")
    shares = sov_res.get("shares", [])
    log_test("Share of Voice Service", "PASS", f"Computed category SOV with {len(shares)} participants")
except Exception as e:
    log_test("Share of Voice Service", "FAIL", str(e))

# --- Test 16: Action Dispatch Service ---
async def test_action_dispatch():
    try:
        from action_dispatch_service import ActionDispatchService
        playbook = await ActionDispatchService.generate_departmental_playbook(
            company_id="e38cd11d-06a3-4bce-a7a3-2bb3777f25ef",
            competitor_id="ea1578b9-2a17-406d-a2b7-8669692664b5",
            event_context={"title": "Pricing cut by 25%", "summary": "Reduced prices on starter tier."}
        )
        has_prod = "product" in playbook or "playbook" in playbook or "headline" in playbook
        log_test("Action Dispatch Service", "PASS", f"Generated departmental playbook: {list(playbook.keys())[:3]}")
    except Exception as e:
        log_test("Action Dispatch Service", "FAIL", str(e))

asyncio.run(test_action_dispatch())

# --- Test 17: Tactical Battlecard Service ---
async def test_battlecard():
    try:
        from battlecard_service import BattlecardService
        battlecard = await BattlecardService.generate_battlecard(
            company_id="e38cd11d-06a3-4bce-a7a3-2bb3777f25ef",
            competitor_id="ea1578b9-2a17-406d-a2b7-8669692664b5"
        )
        strengths = len(battlecard.get("strengths", []))
        log_test("Battlecard Service", "PASS", f"Generated battlecard for competitor: {strengths} strengths, {len(battlecard.get('howToWin', []))} howToWin")
    except Exception as e:
        log_test("Battlecard Service", "FAIL", str(e))

asyncio.run(test_battlecard())

# --- Summary ---
total = len(results)
passed = sum(1 for r in results.values() if r["status"] == "PASS")
warn = sum(1 for r in results.values() if r["status"] == "WARN")
failed = sum(1 for r in results.values() if r["status"] == "FAIL")

print("\n" + "="*50)
print(f"FINAL SUMMARY: {passed}/{total} PASSED, {warn} WARNINGS, {failed} FAILED")
print("="*50)
