# 🛠️ AURA-CI BACKEND: FULL FRONTEND INTEGRATION SPECIFICATION

This document is the **complete, end-to-end technical API contract and integration guide** for the Frontend Engineering team. It details every endpoint, exact request/response schemas, TypeScript interfaces, and the exact UI components/charts to render.

---

## 📑 Quick Navigation
1. [Global API Standards & Authentication](#1-global-api-standards--authentication)
2. [Complete TypeScript Type Definitions](#2-complete-typescript-type-definitions)
3. [Page-by-Page Architecture & UI Component Map](#3-page-by-page-architecture--ui-component-map)
   - [Page 1: Onboarding & Discovery Wizard](#page-1-onboarding--competitor-discovery)
   - [Page 2: Executive Boardroom & Strategy Brief](#page-2-executive-boardroom--strategy-brief)
   - [Page 3: Competitor Detail & Tactical Sales Battlecard](#page-3-competitor-detail--tactical-sales-battlecard)
   - [Page 4: Category Pricing Matrix & Boundary Benchmarks](#page-4-category-pricing-matrix--boundary-benchmarks)
   - [Page 5: 2D Spatial Positioning Radar](#page-5-2d-spatial-positioning-radar)
   - [Page 6: Commercial Win/Loss Deal Intelligence](#page-6-commercial-winloss-deal-intelligence)
   - [Page 7: Machine Learning & Topic Lab](#page-7-machine-learning--topic-lab)
   - [Page 8: Autonomous GTM Action Center (Jira & WhatsApp)](#page-8-autonomous-gtm-action-center-jira--whatsapp)
4. [Master API Endpoint Reference (All 20 Endpoints)](#4-master-api-endpoint-reference)

---

## 1. Global API Standards & Authentication

* **Local Development Base URL:** `http://localhost:8000`
* **Production Base URL:** `https://your-render-app.onrender.com`
* **Interactive Swagger UI:** `http://localhost:8000/docs`
* **Authentication Scheme:** Standard HTTP Bearer Token.
  ```http
  Authorization: Bearer <supabase_jwt_token>
  Content-Type: application/json
  ```
* **Global Error Format:**
  ```json
  {
    "detail": "Descriptive error message string"
  }
  ```

---

## 2. Complete TypeScript Type Definitions

Save this as `src/types/api.ts` in your frontend project:

```typescript
// ============================================================================
// CORE ENTITIES
// ============================================================================

export interface CompanyProfile {
  id: string;
  company_name: string;
  industry: string;
  website_url?: string;
  description: string;
  products_or_services?: string;
  setup_status: 'PENDING' | 'COMPLETED';
  setup_current_step: number;
  weekly_brief?: string;
  weekly_brief_generated_at?: string;
  top_threats?: Array<{
    threat: string;
    competitor: string;
    urgency: 'HIGH' | 'MEDIUM' | 'LOW';
    evidence: string;
    recommendedAction: string;
  }>;
  opportunities?: Array<{
    opportunity: string;
    basis: string;
    potentialImpact: string;
    recommendedAction: string;
  }>;
  strategic_recommendations?: Array<{
    area: string;
    action: string;
    rationale: string;
    expectedOutcome: string;
  }>;
  competitive_velocity?: string;
}

export interface Competitor {
  id: string;
  name: string;
  website_url: string;
  description?: string;
  competitive_score: number;
  confidence_score: number;
  is_accepted: boolean;
  action: 'PENDING' | 'ACCEPTED' | 'REJECTED';
  research_status: 'IDLE' | 'RESEARCHING' | 'COMPLETED';
  created_at: string;
}

// ============================================================================
// QUANTITATIVE & MATHEMATICAL SIGNALS
// ============================================================================

export interface FlagshipAndBoundaries {
  competitorId: string;
  competitorName: string;
  flagshipProduct: {
    name: string;
    confidenceScore: number;
    extractionMethod: string;
  };
  pricingMinima: number | null;
  pricingMaxima: number | null;
  pricingMedian: number | null;
  pricingTiersDetected: string[];
  whitespaceGap: {
    hasGap: boolean;
    gapStart: number | null;
    gapEnd: number | null;
    gapSize: number;
  };
  mathematicalExtrema: {
    activityMaximaPeaks: Array<{
      weekIndex: number;
      eventCount: number;
      prominence: number;
    }>;
    sentimentMinimaTroughs: Array<{
      weekIndex: number;
      sentimentScore: number;
      troughSeverity: number;
    }>;
    signalVolatility: number;
    momentumVector: 'ACCELERATING' | 'STEADY' | 'STAGNANT';
  };
}

export interface CategoryPricingMatrix {
  companyId: string;
  categoryBenchmarks: {
    marketFloorMinima: number | null;
    marketCeilingMaxima: number | null;
    categoryMedian: number | null;
    pricingSpread: number | null;
  };
  competitorMatrix: Array<{
    id: string;
    name: string;
    flagshipProduct: string;
    priceMinima: number | null;
    priceMaxima: number | null;
    pricingTiers: string[];
    positioningTier: 'FREEMIUM_ENTRY' | 'MID_MARKET' | 'PREMIUM_ENTERPRISE' | 'ENTERPRISE_CUSTOM';
  }>;
  macroWhitespaceGaps: Array<{
    unoccupiedTierRange: [number, number];
    gapSize: number;
    opportunityRationale: string;
  }>;
  strategicRecommendation: string;
}

// ============================================================================
// 2D SPATIAL POSITIONING RADAR
// ============================================================================

export interface PositioningNode {
  id: string;
  name: string;
  isHomeTeam: boolean;
  x: number; // 0.0 to 100.0 (Market Tier / Price)
  y: number; // 0.0 to 100.0 (Product Scope / Platform Breadth)
  quadrant: 'ENTERPRISE_PLATFORM' | 'PREMIUM_SPECIALIST' | 'DISRUPTIVE_CHALLENGER' | 'LIGHTWEIGHT_POINT_SOLUTION';
  marketFocus: string;
  productScope: string;
}

export interface PositioningRadarData {
  companyId: string;
  homeTeam: PositioningNode;
  competitors: PositioningNode[];
  threatDistances: Array<{
    competitorId: string;
    name: string;
    euclideanDistance: number;
    threatSeverity: 'CRITICAL_ENCROACHMENT' | 'HIGH_OVERLAP' | 'MODERATE_PROXIMITY' | 'LOW_THREAT';
    strategicAlert: string;
  }>;
  whiteSpaceOpportunities: Array<{
    targetCoordinates: { x: number; y: number };
    quadrant: string;
    clearanceDistance: number;
    strategicRationale: string;
  }>;
  strategicPositioningSummary: string;
}

// ============================================================================
// COMMERCIAL WIN/LOSS DEAL INTELLIGENCE
// ============================================================================

export interface DealOutcomePayload {
  competitorId: string;
  outcome: 'WON' | 'LOST' | 'TIED';
  dealValue?: number;
  primaryReason?: 'PRICING' | 'FEATURE_GAP' | 'BRAND_TRUST' | 'USABILITY' | 'SPEED';
  competitorStrength?: string;
  prospectName?: string;
  notes?: string;
}

export interface DealAnalytics {
  companyId: string;
  totalDealsLogged: number;
  overallWinRate: number; // Percentage, e.g. 66.7
  pipelineWon: number;
  pipelineLost: number;
  pipelineAtRisk: number;
  headToHeadMatrix: Array<{
    competitorId: string;
    competitorName: string;
    totalDeals: number;
    won: number;
    lost: number;
    tied: number;
    winRate: number;
    primaryLossReason: string;
  }>;
  lossReasonDistribution: Record<string, number>;
  strategicRecommendation: string;
}

// ============================================================================
// COMMUNITY SIGNALS & MARKET SHARE OF VOICE
// ============================================================================

export interface CommunityVoiceData {
  competitorName: string;
  netSentimentScore: number; // -1.0 to +1.0
  totalDiscussionsAnalyzed: number;
  topCustomerComplaints: Array<{
    topic: string;
    frequency: number;
    sentimentScore: number;
    sampleQuote: string;
  }>;
  customerPraiseHighlights: string[];
  recentThreads: Array<{
    platform: 'REDDIT' | 'HACKER_NEWS';
    title: string;
    url: string;
    score: number;
    commentsCount: number;
    publishedDate: string;
  }>;
}

export interface ShareOfVoiceData {
  companyId: string;
  totalAnalyzedMentions: number;
  categoryBuzzLeader: string;
  ourShareOfVoice: number;
  shareOfVoiceRanking: Array<{
    id: string;
    name: string;
    isHomeTeam: boolean;
    mentionsRecorded: number;
    shareOfVoicePct: number;
    marketPresenceTier: 'MARKET_DOMINATOR' | 'STRONG_CONTENDER' | 'NICHE_PRESENCE' | 'ACTIVE_PLAYER';
    buzzMomentum: 'HIGH_BUZZ' | 'STEADY' | 'QUIET' | 'ACCELERATING';
  }>;
  strategicInsight: string;
}

// ============================================================================
// GITHUB TECHNICAL VELOCITY
// ============================================================================

export interface GitHubSignalsData {
  repo: string;
  hasPublicRepo: boolean;
  stars: number;
  forks: number;
  openIssues: number;
  lastPushedAt: string;
  velocityClassification: 'HYPER_ACTIVE_DEVELOPMENT' | 'HEALTHY_STEADY_CADENCE' | 'LOW_COMMUNITY_VELOCITY';
  recentReleases: Array<{
    tag: string;
    name: string;
    publishedAt: string;
    htmlUrl: string;
  }>;
  techStack: Array<{
    language: string;
    percentage: number;
  }>;
  summary: string;
}

// ============================================================================
// MACHINE LEARNING & HUGGING FACE MODELS
// ============================================================================

export interface MLAnomalyData {
  competitorName: string;
  hasAnomalies: boolean;
  isLatestPeriodAnomalous: boolean;
  totalObservationsAnalyzed: number;
  totalAnomaliesDetected: number;
  anomalies: Array<{
    date: string;
    index: number;
    anomalyScore: number;
    anomalyType: 'VELOCITY_EXPANSION_ANOMALY' | 'UNUSUAL_STAGNATION_ANOMALY' | 'SENTIMENT_CRISIS_ANOMALY' | 'HIGH_IMPACT_DISRUPTION' | 'STRUCTURAL_MARKET_ANOMALY';
    vector: {
      eventCount: number;
      avgImpact: number;
      sentiment: number;
      tierCount: number;
    };
    description: string;
    severity: 'CRITICAL' | 'HIGH';
  }>;
  modelMetadata: {
    algorithm: string;
    n_estimators: number;
    contamination: number;
    features: string[];
  };
  summary: string;
}

export interface MLTopicClusterData {
  totalDocumentsClustered: number;
  kClusters: number;
  algorithm: string;
  dominantTheme: string;
  clusters: Array<{
    clusterId: number;
    theme: string;
    topKeyphrases: string[];
    documentCount: number;
    categorySharePct: number;
    sampleDocuments: Array<{
      title: string;
      competitor: string;
      impactScore: number;
      summary: string;
    }>;
  }>;
  summary: string;
}

// ============================================================================
// AUTONOMOUS GTM ACTION DISPATCH
// ============================================================================

export interface DepartmentalPlaybook {
  competitorId: string;
  competitorName: string;
  generatedAt: string;
  eventSummary: string;
  productDirective: {
    jiraIssueTitle: string;
    userStory: string;
    acceptanceCriteria: string[];
    priority: 'CRITICAL' | 'HIGH' | 'MEDIUM';
    recommendedSprint: string;
  };
  salesDirective: {
    liveCounterScript: string;
    coldOutreachSnippet: string;
    pricingCounter: string;
  };
  marketingDirective: {
    adCampaignHeadline: string;
    landingPageAngle: string;
    contentTitle: string;
  };
  executiveDirective: {
    strategicDecision: string;
    revenueAtRisk: string;
  };
}

export interface JiraCreatePayload {
  jira_domain: string;
  email: string;
  api_token: string;
  project_key: string;
  summary: string;
  description: string;
  issue_type?: 'Task' | 'Story' | 'Bug';
  priority?: 'Highest' | 'High' | 'Medium' | 'Low';
}

export interface WhatsAppAlertPayload {
  recipient_phone: string;
  alert_text: string;
  custom_webhook_url?: string;
}
```

---

## 3. Page-by-Page Architecture & UI Component Map

### Page 1: Onboarding & Competitor Discovery
* **Target Route:** `/onboarding`
* **Workflow:**
  1. User submits company profile via `POST /api/company/profile`.
  2. Frontend calls `POST /api/competitors/discover` to fetch recommended competitors.
  3. User reviews competitor cards and calls:
     - `POST /api/competitors/{id}/accept` (Accept rival into monitor pool)
     - `POST /api/competitors/{id}/reject` (Dismiss rival)

---

### Page 2: Executive Boardroom & Strategy Brief
* **Target Route:** `/dashboard` or `/boardroom`
* **Data Sources:**
  - `GET /api/intelligence/strategy-brief` (Strategic memo, top threats, opportunities)
  - `GET /api/reports/boardroom-pdf` (Binary stream for multi-page PDF download)
* **Code Example for PDF Download:**
  ```typescript
  const handleDownloadPDF = async () => {
    const response = await fetch('/api/reports/boardroom-pdf', {
      headers: { Authorization: `Bearer ${token}` }
    });
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Executive_Boardroom_Report.pdf`;
    a.click();
  };
  ```

---

### Page 3: Competitor Detail & Tactical Sales Battlecard
* **Target Route:** `/competitors/:id`
* **Data Sources:**
  - `GET /api/competitors/{id}/battlecard` (Quick dismissals, landmines to lay, win/lose split)
  - `GET /api/competitors/{id}/signals` (TF-IDF Flagship product, Min/Max pricing, Activity wave peaks)
  - `GET /api/competitors/{id}/community-signals` (Reddit/HN sentiment, top customer complaints)
  - `GET /api/competitors/{id}/github-signals` (Open source releases, stargazer velocity, language stack)

---

### Page 4: Category Pricing Matrix & Boundary Benchmarks
* **Target Route:** `/pricing-matrix`
* **Data Sources:**
  - `GET /api/competitors/pricing-matrix` (Side-by-side tiers, Market Floor $P_{min}$, Ceiling $P_{max}$, Whitespace voids)
  - `GET /api/competitors/{id}/deltas` (Step-function price hike/cut deltas over time)

---

### Page 5: 2D Spatial Positioning Radar
* **Target Route:** `/radar`
* **Data Sources:**
  - `GET /api/competitors/positioning-radar`
* **Recommended Visual Component:** 
  - 2D Scatter / Bubble chart (X: Price Tier, Y: Scope).
  - 4 quadrants: *Enterprise Giants*, *Disruptive Challengers*, *Premium Specialists*, *Lightweight Point Tools*.
  - Draw dotted Euclidean threat lines to rivals with distance $< 25$ (`CRITICAL ENCROACHMENT`).

---

### Page 6: Commercial Win/Loss Deal Intelligence
* **Target Route:** `/deals`
* **Data Sources:**
  - `GET /api/deals/analytics` (Win rate %, pipeline revenue lost, primary loss reasons)
  - `POST /api/deals/outcome` (Modal form to record deal outcomes: `WON`, `LOST`, `TIED`)

---

### Page 7: Machine Learning & Topic Lab
* **Target Route:** `/ml-lab`
* **Data Sources:**
  - `GET /api/competitors/{id}/ml-anomalies` (IsolationForest statistical anomaly flags)
  - `GET /api/intelligence/ml-clusters` (KMeans thematic clusters of market events)
  - `POST /api/ml/semantic-similarity` (Hugging Face MiniLM dense semantic similarity)
  - `POST /api/ml/business-sentiment` (Hugging Face FinBERT financial sentiment)

---

### Page 8: Autonomous GTM Action Center (Jira & WhatsApp)
* **Target Route:** `/action-center` or `/playbooks`
* **Data Sources:**
  - `POST /api/actions/playbook` (Generates 4-department tactical playbook for Product, Sales, Marketing, Exec)
  - `POST /api/actions/jira` (Directly creates a ticket in Atlassian Jira Cloud via REST API)
  - `POST /api/actions/whatsapp` (Dispatches an urgent alert to WhatsApp / Mobile Webhook)

---

## 4. Master API Endpoint Reference

| # | Method | Path | Description | Key Request Params |
|---|:---:|---|---|---|
| **1** | `GET` | `/api/competitors/{id}/battlecard` | 1-page tactical sales battlecard | `id` (path) |
| **2** | `GET` | `/api/competitors/{id}/signals` | Flagship product, Price Min/Max, Peaks | `id` (path) |
| **3** | `GET` | `/api/competitors/pricing-matrix` | Category pricing benchmarks & whitespace | None |
| **4** | `GET` | `/api/competitors/{id}/snapshots` | Historical state snapshot history | `id` (path) |
| **5** | `GET` | `/api/competitors/{id}/deltas` | Step-function price shifts & pivots | `id` (path) |
| **6** | `GET` | `/api/competitors/positioning-radar` | 2D coordinates, quadrants & encroachment | None |
| **7** | `POST`| `/api/deals/outcome` | Record a commercial deal result | Body: `DealOutcomePayload` |
| **8** | `GET` | `/api/deals/analytics` | Win rates, revenue lost & loss reasons | None |
| **9** | `GET` | `/api/competitors/{id}/community-signals`| Live Reddit & Hacker News customer voice | `id` (path) |
| **10**| `GET` | `/api/reports/boardroom-pdf` | Downloadable executive boardroom PDF | Streams `application/pdf` |
| **11**| `GET` | `/api/competitors/share-of-voice` | Category Share of Voice % rankings | None |
| **12**| `GET` | `/api/competitors/{id}/github-signals` | Open-source release cadence & tech stack | `id` (path) |
| **13**| `GET` | `/api/competitors/{id}/ml-anomalies` | IsolationForest statistical anomaly flags | `id` (path) |
| **14**| `GET` | `/api/intelligence/ml-clusters` | KMeans ($k=3..5$) thematic clusters | `num_clusters` (query) |
| **15**| `POST`| `/api/ml/semantic-similarity` | Hugging Face dense semantic similarity | Body: `{ source_text, candidate_texts }` |
| **16**| `POST`| `/api/ml/business-sentiment` | Hugging Face FinBERT business sentiment | Body: `{ text }` |
| **17**| `POST`| `/api/actions/playbook` | Generate 4-department tactical playbook | Body: `{ competitor_id, event_context }` |
| **18**| `POST`| `/api/actions/jira` | Directly create ticket in Jira Cloud REST API | Body: `JiraCreatePayload` |
| **19**| `POST`| `/api/actions/whatsapp` | Dispatch WhatsApp / Webhook alert | Body: `WhatsAppAlertPayload` |
| **20**| `GET` | `/api/tasks/{id}/jira-link` | Fallback browser-redirect Jira URL | `id` (path) |
