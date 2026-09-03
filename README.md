<div align="center">
  <img src="https://img.icons8.com/color/96/000000/artificial-intelligence.png" alt="AI Icon"/>
  <h1>AI Competitive Intelligence Platform</h1>
  <p>
    <strong>Automated competitor discovery, live web monitoring, and AI-synthesized strategy briefs.</strong>
  </p>
  
  <p>
    <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" /></a>
    <a href="https://python.org/"><img src="https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" /></a>
    <a href="https://supabase.com/"><img src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase" /></a>
    <a href="https://groq.com/"><img src="https://img.shields.io/badge/Groq-FF3366?style=for-the-badge&logo=groq&logoColor=white" alt="Groq AI" /></a>
  </p>
</div>

---

## 📖 Table of Contents
- [About the Project](#-about-the-project)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Core Features](#-core-features)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
- [API Reference](#-api-reference)
- [Background Workers](#-background-workers)

---

## 🚀 About the Project

This backend powers a real-time Competitive Intelligence (CI) dashboard. Rather than manually tracking competitors, the system uses semantic search (**Exa AI**) and live web scraping (**Jina AI**) to autonomously identify market rivals. It then leverages LLMs (**Groq / LLaMA 3**) to read their websites, track news events, and generate actionable executive strategy briefs dynamically.

---

## 🛠 Architecture & Tech Stack

| Component | Technology | Purpose |
| --- | --- | --- |
| **API Framework** | FastAPI (Python) | High-performance, async API routing. |
| **Database** | Supabase (PostgreSQL) | Stores users, companies, competitors, and scraped intelligence. |
| **AI / LLM** | Groq (`llama-3.3-70b-versatile`) | Rapid semantic reasoning, scoring, and strategy brief generation. |
| **Scraping** | Jina Reader API | Bypasses paywalls and extracts clean markdown from raw URLs. |
| **Search** | Exa AI / Serper / NewsAPI | Discovers competitor domains and monitors daily news events. |

---

## ✨ Core Capabilities & Mathematical Engines

- 🧠 **NLP Flagship Product Discovery:** Uses TF-IDF N-Gram Prominence over DOM headers and navigation to extract the competitor's true core revenue driver vs side-features.
- 📈 **Mathematical Signal Processing (Maxima & Minima):** Applies `scipy.signal.find_peaks` over event and sentiment time-series to detect activity surges (PR waves, product launches) and stagnation/churn troughs.
- 🏷️ **Pricing Boundaries & Whitespace:** Deterministically computes Market Floor ($P_{min}$), Enterprise Ceiling ($P_{max}$), Category Median, and uncontested whitespace gaps.
- ⏳ **Historical Snapshots & Step-Function Deltas:** Tracks immutable weekly state to compute exact price hikes, fee drops, and flagship product pivots across time.
- 🎯 **2D Spatial Positioning Radar:** Projects all rivals onto a 2D coordinate grid (Price Tier vs Product Scope), calculating Euclidean threat encroachment and open market niches.
- ⚔️ **Tactical Sales Battlecards:** 1-page sales weapons with quick dismissals, landmines to lay, where we win vs where they win, and pricing counters.
- 💼 **Win/Loss Deal Intelligence:** Logs commercial sales outcomes to compute head-to-head win rates, revenue at risk, and primary loss drivers.
- 🗣️ **Community Voice Ingestion:** Live Reddit and Hacker News customer complaints, praise, and net sentiment.
- 📊 **Share of Voice (SOV) & Buzz Momentum:** Quantifies conversational footprint percentage and categorizes buzz momentum.
- 💻 **GitHub Technical Velocity:** Tracks open-source releases, stargazer growth, and tech stack distribution.
- 📄 **Executive Boardroom PDF Export:** Generates multi-page vector PDF briefing documents with ReportLab for board meetings.
- 🚨 **Autonomous Real-Time Webhooks:** Instant Slack Block Kit notifications dispatched when impact score $\ge 80$ or pricing shifts occur.

---

## 🚦 Getting Started

### Prerequisites
- Python 3.10+
- A Supabase Project
- API Keys for Groq, Exa, Serper, and NewsAPI

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/ai-backend.git
   cd ai-backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the Database:**
   Ensure your Supabase project is active and run the provided SQL migrations to create the `companies`, `competitors`, `monitoring_jobs`, `documents`, and `audit_logs` tables.

### Environment Variables
Copy the example config and fill in your keys:
```bash
cp .env.example .env
```
Inside your `.env` file:
```env
# LLM APIs
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
EXTRACTION_MODEL=llama-3.1-8b-instant

# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# Search APIs
JINA_API_KEY=your_jina_api_key_here
EXA_API_KEY=your_exa_api_key_here
SERPER_API_KEY=your_serper_api_key_here
NEWS_API_KEY=your_news_api_key_here
```

### Running the Server
Start the development server using Uvicorn:
```bash
uvicorn main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` to view the interactive Swagger API documentation.

---

## 🔌 API Reference

Here are the primary endpoints exposed by the FastAPI server:

<details>
<summary><b>1. Advanced Competitive Intelligence (12 Core Weapons)</b></summary>

- `GET /api/competitors/{id}/battlecard` - Generate a 1-page tactical sales battlecard.
- `GET /api/competitors/{id}/signals` - Mathematical signal processing (maxima, minima, volatility, flagship).
- `GET /api/competitors/pricing-matrix` - Live category pricing grid, benchmarks, and whitespace gaps.
- `GET /api/competitors/{id}/snapshots` - Chronological historical state timeline.
- `GET /api/competitors/{id}/deltas` - Step-function price changes and product pivots.
- `GET /api/competitors/positioning-radar` - 2D spatial coordinate map, quadrant nodes, and encroachment distance.
- `POST /api/deals/outcome` - Record commercial sales deal outcomes (WON, LOST, TIED).
- `GET /api/deals/analytics` - Win rates, revenue at risk, and loss root causes.
- `GET /api/competitors/{id}/community-signals` - Live Reddit & Hacker News customer voice.
- `GET /api/reports/boardroom-pdf` - Downloadable executive boardroom PDF report.
- `GET /api/competitors/share-of-voice` - Category Share of Voice & buzz momentum.
- `GET /api/competitors/{id}/github-signals` - Open-source technical cadence & tech stack.
</details>

<details>
<summary><b>2. Intelligence Feed & Executive Briefs</b></summary>

- `GET /api/intelligence/feed` - Real-time scrolling feed of competitor events.
- `GET /api/intelligence/strategy-brief` - Weekly executive memo synthesizing multi-engine signals.
- `POST /api/intelligence/generate-summary` - Force a manual generation of the Strategy Brief.
</details>

<details>
<summary><b>3. Competitor Management</b></summary>

- `GET /api/competitors` - Retrieve tracked competitors and threat scores.
- `POST /api/competitors/{id}/research` - Trigger deep AI scrape of a competitor.
- `DELETE /api/competitors/{id}` - Archive/Delete a tracked competitor.
- `POST /api/competitors/{id}/accept` - Accept a recommended competitor.
- `POST /api/competitors/{id}/reject` - Reject a recommended competitor.
</details>

---

## ⚙️ Background Workers
Because web scraping and LLM processing take time, the system heavily relies on `asyncio.create_task()`. Long-running tasks like `generate_strategy_brief` are managed safely in memory using an `_active_background_tasks` set to prevent early Python Garbage Collection during API responses. 

<div align="center">
  <i>Built with ❤️ by Amit</i>
</div>
