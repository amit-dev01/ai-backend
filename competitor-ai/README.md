# Competitor Analysis AI

AI-powered competitive intelligence API. Submit a competitor's company name and website URL, and receive a comprehensive, executive-ready analysis report — complete with SWOT, prioritized next steps, and differentiation strategy.

Built with **FastAPI**, **Crawl4AI**, and **Groq** (Llama 3.3 70B / Llama 3.1 8B).

---

## Features

- **Automated web scraping** via Crawl4AI (headless Chromium)
- **Structured data extraction** using Llama 3.1 8B (via Groq)
- **Deep competitive analysis** using Llama 3.3 70B (via Groq) — SWOT, Porter's, positioning
- **Polished Markdown reports** saved to disk and returned via API
- **Best-effort social scraping** (Instagram, LinkedIn, etc.)
- Fully async end-to-end

---

## Project Structure

```
competitor-ai/
├── main.py              # FastAPI app entry
├── scraper.py           # Crawl4AI async scraping
├── extractor.py         # LLM-based data extraction
├── analyzer.py          # LLM-based business analysis
├── prompts.py           # All LLM prompt templates
├── models.py            # Pydantic schemas
├── config.py            # Env + settings
├── requirements.txt
├── .env.example
├── README.md
└── reports/             # Auto-created, stores .md reports
```

---

## Setup

### 1. Clone and enter the project

```bash
cd competitor-ai
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright browser (required by Crawl4AI)

```bash
playwright install chromium
```

### 5. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```env
GROQ_API_KEY=gsk-your-key-here
LLM_MODEL=llama-3.3-70b-versatile
EXTRACTION_MODEL=llama-3.1-8b-instant
```

---

## Running the Server

```bash
python main.py
```

The API will start on **http://localhost:8000** with auto-reload enabled.

Interactive API docs: **http://localhost:8000/docs**

---

## API Endpoints

### Health Check

```
GET /
```

Response:

```json
{
  "status": "ok",
  "service": "competitor-analysis-ai"
}
```

### Analyze Competitor

```
POST /analyze
```

#### Sample Request

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Nike",
    "website_url": "https://www.nike.com",
    "industry": "Athletic Footwear & Apparel",
    "our_company_context": "We are a sustainable athletic wear D2C brand targeting Gen Z.",
    "social_urls": {"instagram": "https://instagram.com/nike"},
    "focus_areas": ["products", "positioning", "social"]
  }'
```

#### Sample Response (excerpt)

```json
{
  "company_name": "Nike",
  "executive_summary": "Nike is a global leader in athletic footwear and apparel ...",
  "snapshot": {
    "Business Model": "D2C + Wholesale",
    "Target Customer": "Athletes and lifestyle consumers aged 16-45",
    "Price Positioning": "Premium",
    "Distribution": "DTC website, Nike App, retail partners",
    "Brand Tone": "Inspirational, performance-driven",
    "Digital Maturity": "9/10 — best-in-class e-commerce, app ecosystem, and content engine"
  },
  "strengths": [
    "Brand equity — globally recognized, aspirational brand with decades of athlete endorsements.",
    "DTC flywheel — Nike.com + SNKRS app drive high-margin direct sales with deep personalization."
  ],
  "weaknesses": [
    "Sustainability messaging is surface-level — opens door for authentic eco-first challengers.",
    "Gen Z engagement relies on legacy brand equity rather than community-driven co-creation."
  ],
  "opportunities": [
    "Position on radical transparency in supply chain — Nike's sustainability page is generic.",
    "Build a TikTok-native brand voice — Nike's social is polished but not participatory."
  ],
  "threats": [
    "Nike's DTC push means they're investing billions in the same channel we need — Severity: High.",
    "Athlete endorsement deals create cultural moats that are expensive to replicate — Severity: Med."
  ],
  "swot": {
    "Strengths": ["..."],
    "Weaknesses": ["..."],
    "Opportunities": ["..."],
    "Threats": ["..."]
  },
  "next_steps": [
    {
      "priority": "P0 (this week)",
      "action": "Audit our sustainability claims page vs. Nike's",
      "rationale": "Nike's page is generic — we can differentiate with specifics",
      "owner_suggestion": "Marketing",
      "expected_impact": "Unique positioning angle, medium brand lift"
    }
  ],
  "differentiation_strategy": "Position as the anti-Nike: small-batch, transparent, community-owned ...",
  "full_markdown_report": "# Competitive Intelligence Report: Nike\n...",
  "generated_at": "2026-07-29T11:00:00Z"
}
```

---

## How It Works

1. **Scrape** — Crawl4AI fetches the competitor's website (and optionally social pages) using a headless Chromium browser.
2. **Extract** — Llama 3.1 8B (via Groq) parses the raw Markdown into structured business signals (products, pricing, positioning, tech stack, etc.).
3. **Analyze** — Llama 3.3 70B (via Groq) applies competitive frameworks (SWOT, Porter's) to produce actionable strategic insights.
4. **Format** — The analysis is converted into a polished Markdown report suitable for executive review.
5. **Deliver** — The API returns both the structured JSON and the full Markdown report. A copy is saved to `reports/`.

---

## Configuration

| Variable           | Default                      | Description                                    |
| ------------------ | ---------------------------- | ---------------------------------------------- |
| `GROQ_API_KEY`     | *(required)*                 | Your Groq API key                              |
| `LLM_MODEL`        | `llama-3.3-70b-versatile`    | Model used for competitive analysis            |
| `EXTRACTION_MODEL` | `llama-3.1-8b-instant`       | Model used for data extraction & report format |

---

## Notes

- **Social scraping** is best-effort. Most social platforms (Instagram, LinkedIn, Twitter) actively block automated scraping. The API will gracefully return empty content for blocked platforms.
- **Content cap**: Scraped content is capped at 50,000 characters before being sent to the LLM to avoid exceeding token limits.
- **Reports** are saved to the `reports/` directory with the naming pattern `{company-slug}_{timestamp}.md`.

---

## License

MIT
