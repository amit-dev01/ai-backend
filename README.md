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

## ✨ Core Features

- 🕵️ **Automated Competitor Discovery:** Enter your company description, and the AI autonomously finds and ranks up to 10 relevant market rivals.
- 📡 **Live News Monitoring:** Scheduled background jobs that scan the web for recent competitor activity (product launches, pricing changes, PR announcements).
- 🧠 **AI Strategy Briefs:** Synthesizes hundreds of intelligence documents from the past 7 days into a comprehensive report outlining threats, opportunities, and strategic recommendations.
- ⚡ **Asynchronous Pipelines:** Robust background processing utilizing `asyncio` to prevent timeouts on long-running LLM scraping tasks.

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
<summary><b>Authentication & Onboarding</b></summary>

- `POST /api/auth/signup` - Register a new organization owner.
- `POST /api/auth/login` - Authenticate and retrieve JWT.
- `POST /api/company/profile` - Set the initial company profile to bootstrap discovery.
</details>

<details>
<summary><b>Competitor Management</b></summary>

- `GET /api/competitors` - Retrieve tracked competitors and their threat scores.
- `POST /api/competitors/{id}/research` - Trigger a deep AI scrape of a specific competitor.
- `DELETE /api/competitors/{id}` - Archive/Delete a tracked competitor.
</details>

<details>
<summary><b>Intelligence & Strategy</b></summary>

- `GET /api/intelligence/feed` - Infinite scrolling feed of recent competitor news events.
- `GET /api/intelligence/strategy-brief` - Retrieve the latest weekly AI executive summary.
- `POST /api/intelligence/generate-summary` - Force a manual generation of the Strategy Brief.
</details>

---

## ⚙️ Background Workers
Because web scraping and LLM processing take time, the system heavily relies on `asyncio.create_task()`. Long-running tasks like `generate_strategy_brief` are managed safely in memory using an `_active_background_tasks` set to prevent early Python Garbage Collection during API responses. 

<div align="center">
  <i>Built with ❤️ by Amit</i>
</div>
