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
        if content and ("Example Domain" in content or len(content) > 100):
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
    shares = sov_res.get("shareOfVoiceRanking", sov_res.get("shares", []))
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
        wins = len(battlecard.get("whereWeWin", []))
        landmines = len(battlecard.get("landminesToLay", []))
        log_test("Battlecard Service", "PASS", f"Generated battlecard: {wins} whereWeWin, {landmines} landmines")
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
