# 🌌 Aetheris — Autonomous Competitive Intelligence Platform

A full-stack, AI-powered competitive intelligence and market telemetry platform.

---

## 📁 Repository Structure

```
ai-backend/
├── frontend/     # React 18 + Vite + TailwindCSS Dashboard UI
│   ├── src/      # UI Components, Pages, and Hooks
│   ├── package.json
│   └── README.md
└── backend/      # FastAPI Autonomous Intelligence & Analytics Engine
    ├── main.py   # API Gateway & Routes
    ├── data/     # Mock data and seed signals
    ├── requirements.txt
    └── README.md
```

---

## 🚀 Quick Start

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Refer to [backend/README.md](backend/README.md) for full backend documentation, architecture details, and environment configurations.

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Refer to [frontend/README.md](frontend/README.md) for frontend setup, environment variables, and UI components.
