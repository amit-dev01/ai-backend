<div align="center">
  
  # 🌌 Aetheris
  
  **AI-Powered Business & Competitive Intelligence Agent**

  [![React](https://img.shields.io/badge/React-18.x-blue?style=for-the-badge&logo=react)](https://reactjs.org/)
  [![Vite](https://img.shields.io/badge/Vite-5.x-646CFF?style=for-the-badge&logo=vite)](https://vitejs.dev/)
  [![TailwindCSS](https://img.shields.io/badge/Tailwind-3.x-38B2AC?style=for-the-badge&logo=tailwind-css)](https://tailwindcss.com/)
  [![FastAPI Backend](https://img.shields.io/badge/API-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)

  *Aetheris provides a modern, glassmorphism-inspired dashboard to track competitors, consume real-time market intelligence, and generate AI-driven strategic briefs.*

</div>

<br />

## 📖 Table of Contents
- [✨ Key Features](#-key-features)
- [🛠️ Tech Stack](#-tech-stack)
- [📦 Installation & Setup](#-installation--setup)
- [⚙️ Environment Variables](#️-environment-variables)
- [📂 Project Architecture](#-project-architecture)
- [🤝 Integration Details](#-integration-details)

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **🔒 Secure Authentication** | Full JWT-based login and signup flow directly integrated with the backend. |
| **🏢 Smart Onboarding** | A guided setup wizard to capture company profile, target audience, and industry goals. |
| **📊 Competitor Dashboard** | Track direct, indirect, and emerging competitors. Features AI-powered auto-discovery and deep research background jobs. |
| **📰 Intelligence Feed** | A real-time, filterable feed of intelligence events regarding competitors, categorized by impact (Critical, High, Medium, Low). |
| **🧠 AI Strategy Briefs** | Manually trigger or auto-generate deep weekly strategy briefs with top threats, opportunities, and actionable recommendations. |
| **⚙️ Dynamic Settings** | Manage monitoring preferences, update company profiles, and toggle smart alerts on the fly. |

---

## 🛠️ Tech Stack

This project was built with modern web technologies prioritizing performance and developer experience:

- **Framework**: [React 18](https://reactjs.org/) + [Vite](https://vitejs.dev/) for lightning-fast HMR and building.
- **Styling**: [TailwindCSS v3](https://tailwindcss.com/) for rapid, utility-first UI development.
- **Icons**: [Lucide React](https://lucide.dev/) for clean, consistent iconography.
- **State Management**: React Hooks & Context API (`DbContext`).
- **Data Fetching**: Custom native `fetch` wrapper (`api.js`) with automatic JWT injection.

---

## 📦 Installation & Setup

Follow these steps to get a local copy up and running.

### 1. Clone the repository
```bash
git clone https://github.com/amit-dev01/Aetheris_1.git
cd Aetheris_1
```

### 2. Install NPM packages
```bash
npm install
```

### 3. Start the Development Server
```bash
npm run dev
```
> The application will typically start on `http://localhost:5173`.

### 4. Build for Production
```bash
npm run build
```
> Production-ready static files will be placed in the `/dist` directory.

---

## ⚙️ Environment Variables

To run this project, you will need to add the following environment variable to your `.env` file in the root directory. This tells the frontend where the Aetheris FastAPI backend is located.

```env
# The base URL of your FastAPI backend
VITE_API_BASE_URL=https://ai-backend-zfq1.onrender.com
```

---

## 📂 Project Architecture

```text
src/
├── api.js                   # Centralized API service (auth, error handling, endpoints)
├── constants.js             # Shared data schemas (e.g. industry dropdown options)
├── App.jsx                  # Main application shell, routing, and Context Provider
├── index.css                # Global Tailwind styles & dark mode definitions
└── components/              
    ├── AIAgentModal.jsx     # Global search/agent modal interface
    ├── AIStrategySection.jsx# Weekly AI Strategy Brief UI
    ├── CompetitorsSection.jsx # Competitor management dashboard
    ├── MarketIntelligenceSection.jsx # Intelligence news feed
    ├── OnboardingFlow.jsx   # Multi-step setup wizard
    ├── ProcessingScreen.jsx # Loading screen for AI discovery
    └── SettingsSection.jsx  # Company & monitoring preferences
```

---

## 🤝 Integration Details

This frontend is designed to be highly reactive to the backend state:
- **Smart Polling:** Long-running backend AI tasks (like deep competitor research or intelligence generation) trigger an active polling loop on the frontend that hits `GET /api/intelligence/jobs` every 10 seconds to detect completion.
- **Global Error Handling:** All HTTP 400 and 500 errors are caught centrally in `api.js` and pushed to the UI via an integrated `showToast` alert system.
- **Dark Mode Native:** The UI listens to system preferences via `matchMedia` and includes a manual dark mode toggle, instantly shifting Tailwind classes globally.

<br />

<div align="center">
  <i>Made with ❤️ by Amit</i>
</div>
