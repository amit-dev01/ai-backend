# 🛠️ AURA-CI BACKEND: MASTER FRONTEND INTEGRATION SPECIFICATION

This document is the **definitive, end-to-end technical API contract and frontend implementation guide** for the Frontend Engineering team. It reflects the live production backend deployed on Render, mapping every endpoint, exact request/response schemas, TypeScript interfaces, and UI widget integrations.

---

## 📑 Table of Contents
1. [Global API Standards, Authentication & Environments](#1-global-api-standards--authentication)
2. [Complete TypeScript Type Definitions (`src/types/api.ts`)](#2-complete-typescript-type-definitions)
3. [Page-by-Page Architecture & UI Integration Guide (10 Pages)](#3-page-by-page-architecture--ui-integration-guide)
   - [Page 1: Authentication & Company Onboarding](#page-1-authentication--company-onboarding)
   - [Page 2: Competitor Discovery & Review Center](#page-2-competitor-discovery--review-center)
   - [Page 3: Executive Boardroom & Strategic Brief (PDF Export)](#page-3-executive-boardroom--strategic-brief)
   - [Page 4: Tactical Sales Battlecard & Deep Signals](#page-4-tactical-sales-battlecard--deep-signals)
   - [Page 5: Category Pricing Matrix & Whitespace Explorer](#page-5-category-pricing-matrix--whitespace-explorer)
   - [Page 6: 2D Spatial Positioning Radar & Threat Encroachment](#page-6-2d-spatial-positioning-radar)
   - [Page 7: Commercial Win/Loss Deal Intelligence](#page-7-commercial-winloss-deal-intelligence)
   - [Page 8: Machine Learning & NLP Topic Lab](#page-8-machine-learning--nlp-topic-lab)
   - [Page 9: Autonomous Action Center & Tasks Kanban (Jira & WhatsApp)](#page-9-autonomous-action-center--tasks-kanban)
   - [Page 10: Live Intelligence Feed, Trends & Monitoring Jobs](#page-10-live-intelligence-feed-trends--monitoring-jobs)
4. [Master 52-Endpoint API Reference Table](#4-master-52-endpoint-api-reference-table)
5. [Frontend Error Handling & Axios / Fetch Interceptor Setup](#5-frontend-error-handling--client-setup)

---

## 1. Global API Standards & Authentication

### Environments & Endpoints
* **Production Base URL (Live on Render):** `https://ai-backend-zfq1.onrender.com`
* **Interactive Swagger UI Docs:** [https://ai-backend-zfq1.onrender.com/docs](https://ai-backend-zfq1.onrender.com/docs)
* **Raw OpenAPI Specification JSON:** [https://ai-backend-zfq1.onrender.com/openapi.json](https://ai-backend-zfq1.onrender.com/openapi.json)
* **Local Development Base URL:** `http://localhost:8000`

### Authentication Scheme
All protected endpoints require an `Authorization` header containing the Supabase JWT Bearer token obtained from `/api/auth/login` or `/api/auth/signup`:

```http
Authorization: Bearer <supabase_jwt_access_token>
Content-Type: application/json
```

### Standard Error Response Format
Whenever a status code $\ge 400$ is returned, the body matches FastAPI's standard schema:
```json
{
  "detail": "Descriptive explanation of the error"
}
```

---

## 2. Complete TypeScript Type Definitions

Save this file as `src/types/api.ts` in your frontend application. These interfaces match the backend Pydantic models in `models.py` and service responses:

```typescript
// ============================================================================
// 1. AUTH & ONBOARDING
// ============================================================================

export interface AuthRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
}

export interface SetupStatusResponse {
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress: number; // 0 to 100
  currentStep?: string | null;
  completedAt?: string | null;
  error?: string | null;
}

export interface ManualCompetitorInput {
  name: string;
  website?: string | null;
}

export interface CompanyProfilePayload {
  companyName: string;
  website: string;
  industry: string;
  description: string;
  productsOrServices: string[];
  targetCustomers: string;
  companyStage?: string | null;
  companySize?: string | null;
  competitors?: ManualCompetitorInput[] | null;
  excludedCompetitors?: string[] | null;
}

export interface CompanyProfileUpdatePayload {
  companyName?: string | null;
  website?: string | null;
  industry?: string | null;
  description?: string | null;
  companyStage?: string | null;
  companySize?: string | null;
  businessType?: string | null;
  customerSegments?: string[] | null;
  geographicMarkets?: string[] | null;
  productsOrServices?: string | null;
  primaryProblemSolved?: string | null;
}

export interface CompanyProfileResponseCompany {
  id: string;
  companyName: string;
  website: string;
  industry: string;
  setupStatus?: string | null;
  executiveBrief?: string | null;
  mainThreats?: string[] | null;
  keyOpportunity?: string | null;
}

export interface CompanyProfileResponse {
  setupCompleted: boolean;
  company?: CompanyProfileResponseCompany | null;
}

export interface CompanySettingsOut {
  monitoringEnabled: boolean;
  emailDigestEnabled: boolean;
  criticalAlertsEnabled: boolean;
  maxCompetitorsMonitored: number;
  discoveryRunCount: number;
  lastDiscoveryAt?: string | null;
  activeCompetitors: number;
  archivedCompetitors: number;
  jiraDomain?: string | null;
}

export interface CompanySettingsUpdatePayload {
  monitoringEnabled?: boolean | null;
  emailDigestEnabled?: boolean | null;
  criticalAlertsEnabled?: boolean | null;
  maxCompetitorsMonitored?: number | null;
  jiraDomain?: string | null;
}

export interface AuditLogOut {
  id: string;
  action: string;
  entityType: string;
  entityId: string;
  metadata: Record<string, any>;
  createdAt: string;
}

export interface AuditLogResponse {
  activities: AuditLogOut[];
  total: number;
}

// ============================================================================
// 2. COMPETITOR ENTITY & DISCOVERY
// ============================================================================

export interface CompetitorOut {
  id: string;
  name: string;
  website?: string | null;
  description?: string | null;
  type?: 'DIRECT' | 'INDIRECT' | 'EMERGING' | null;
  source?: 'AI_DISCOVERY' | 'MANUAL' | null;
  competitiveScore?: number | null;   // 0 to 100
  confidenceScore?: number | null;    // 0 to 100
  productSimilarity?: number | null;  // 0 to 100
  customerOverlap?: number | null;    // 0 to 100
  marketOverlap?: number | null;      // 0 to 100
  businessModelOverlap?: number | null;
  reason?: string | null;
  isAccepted?: boolean | null;        // null = pending review, true = accepted, false = rejected
  isActive?: boolean | null;          // true = active, false = archived
  customType?: string | null;
  effectiveType?: string | null;
  notes?: string | null;
  lastResearchedAt?: string | null;
  researchStatus?: 'IDLE' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | null;
}

export interface CompetitorsSummary {
  total: number;
  active: number;
  archived: number;
  pendingReview: number;
}

export interface CompetitorsListResponse {
  competitors: CompetitorOut[];
  summary: CompetitorsSummary;
}

export interface CompetitorEditPayload {
  name?: string | null;
  website?: string | null;
  notes?: string | null;
  customType?: string | null;
}

export interface ManualCompetitorRequest {
  name: string;
  website: string;
}

// ============================================================================
// 3. QUANTITATIVE SIGNALS & MATHEMATICAL BOUNDARIES
// ============================================================================

export interface FlagshipProductData {
  name: string;
  confidenceScore: number;
  extractionMethod: string;
}

export interface WhitespaceGapData {
  hasGap: boolean;
  gapStart: number | null;
  gapEnd: number | null;
  gapSize: number;
}

export interface ActivityPeak {
  weekIndex: number;
  eventCount: number;
  prominence: number;
}

export interface SentimentTrough {
  weekIndex: number;
  sentimentScore: number;
  troughSeverity: number;
}

export interface MathematicalExtremaData {
  activityMaximaPeaks: ActivityPeak[];
  sentimentMinimaTroughs: SentimentTrough[];
  signalVolatility: number;
  momentumVector: 'ACCELERATING' | 'STEADY' | 'STAGNANT';
}

export interface CompetitorSignalsResponse {
  competitorId: string;
  competitorName: string;
  flagshipProduct: FlagshipProductData;
  pricingMinima: number | null;
  pricingMaxima: number | null;
  pricingMedian: number | null;
  pricingTiersDetected: string[];
  whitespaceGap: WhitespaceGapData;
  mathematicalExtrema: MathematicalExtremaData;
}

// ============================================================================
// 4. CATEGORY PRICING MATRIX
// ============================================================================

export interface PricingBenchmarks {
  marketFloorMinima: number | null;
  marketCeilingMaxima: number | null;
  categoryMedian: number | null;
  pricingSpread: number | null;
}

export interface CompetitorPricingItem {
  id: string;
  name: string;
  flagshipProduct: string;
  priceMinima: number | null;
  priceMaxima: number | null;
  pricingTiers: string[];
  positioningTier: 'FREEMIUM_ENTRY' | 'MID_MARKET' | 'PREMIUM_ENTERPRISE' | 'ENTERPRISE_CUSTOM';
}

export interface MacroWhitespaceGap {
  unoccupiedTierRange: [number, number];
  gapSize: number;
  opportunityRationale: string;
}

export interface CategoryPricingMatrixResponse {
  companyId: string;
  categoryBenchmarks: PricingBenchmarks;
  competitorMatrix: CompetitorPricingItem[];
  macroWhitespaceGaps: MacroWhitespaceGap[];
  strategicRecommendation: string;
}

// ============================================================================
// 5. 2D SPATIAL POSITIONING RADAR
// ============================================================================

export interface PositioningNode {
  id: string;
  name: string;
  isHomeTeam: boolean;
  x: number; // 0.0 to 100.0 (Market Tier / Price Index)
  y: number; // 0.0 to 100.0 (Product Scope / Breadth Index)
  quadrant: 'ENTERPRISE_PLATFORM' | 'PREMIUM_SPECIALIST' | 'DISRUPTIVE_CHALLENGER' | 'LIGHTWEIGHT_POINT_SOLUTION';
  marketFocus: string;
  productScope: string;
}

export interface ThreatDistanceItem {
  competitorId: string;
  name: string;
  euclideanDistance: number;
  threatSeverity: 'CRITICAL_ENCROACHMENT' | 'HIGH_OVERLAP' | 'MODERATE_PROXIMITY' | 'LOW_THREAT';
  strategicAlert: string;
}

export interface WhitespaceOpportunity {
  targetCoordinates: { x: number; y: number };
  quadrant: string;
  clearanceDistance: number;
  strategicRationale: string;
}

export interface PositioningRadarResponse {
  companyId: string;
  homeTeam: PositioningNode;
  competitors: PositioningNode[];
  threatDistances: ThreatDistanceItem[];
  whiteSpaceOpportunities: WhitespaceOpportunity[];
  strategicPositioningSummary: string;
}

// ============================================================================
// 6. COMMERCIAL WIN/LOSS DEAL INTELLIGENCE
// ============================================================================

export interface DealOutcomePayload {
  competitorId: string;
  outcome: 'WON' | 'LOST' | 'TIED';
  dealValue?: number;
  primaryReason?: 'PRICING' | 'FEATURE_GAP' | 'BRAND_TRUST' | 'USABILITY' | 'SPEED';
  competitorStrength?: string | null;
  prospectName?: string | null;
  notes?: string | null;
}

export interface HeadToHeadStats {
  competitorId: string;
  competitorName: string;
  totalDeals: number;
  won: number;
  lost: number;
  tied: number;
  winRate: number; // e.g. 66.7
  primaryLossReason: string;
}

export interface DealAnalyticsResponse {
  companyId: string;
  totalDealsLogged: number;
  overallWinRate: number;
  pipelineWon: number;
  pipelineLost: number;
  pipelineAtRisk: number;
  headToHeadMatrix: HeadToHeadStats[];
  lossReasonDistribution: Record<string, number>;
  strategicRecommendation: string;
}

// ============================================================================
// 7. COMMUNITY SIGNALS & MARKET SHARE OF VOICE
// ============================================================================

export interface CommunityComplaint {
  topic: string;
  frequency: number;
  sentimentScore: number;
  sampleQuote: string;
}

export interface CommunityThread {
  platform: 'REDDIT' | 'HACKER_NEWS';
  title: string;
  url: string;
  score: number;
  commentsCount: number;
  publishedDate: string;
}

export interface CommunitySignalsResponse {
  competitorName: string;
  netSentimentScore: number; // -1.0 to +1.0
  totalDiscussionsAnalyzed: number;
  topCustomerComplaints: CommunityComplaint[];
  customerPraiseHighlights: string[];
  recentThreads: CommunityThread[];
}

export interface ShareOfVoiceRankingItem {
  id: string;
  name: string;
  isHomeTeam: boolean;
  mentionsRecorded: number;
  shareOfVoicePct: number;
  marketPresenceTier: 'MARKET_DOMINATOR' | 'STRONG_CONTENDER' | 'NICHE_PRESENCE' | 'ACTIVE_PLAYER';
  buzzMomentum: 'HIGH_BUZZ' | 'STEADY' | 'QUIET' | 'ACCELERATING';
}

export interface ShareOfVoiceResponse {
  companyId: string;
  totalAnalyzedMentions: number;
  categoryBuzzLeader: string;
  ourShareOfVoice: number;
  shareOfVoiceRanking: ShareOfVoiceRankingItem[];
  strategicInsight: string;
}

// ============================================================================
// 8. GITHUB TECHNICAL VELOCITY
// ============================================================================

export interface GitHubRelease {
  tag: string;
  name: string;
  publishedAt: string;
  htmlUrl: string;
}

export interface TechStackItem {
  language: string;
  percentage: number;
}

export interface GitHubSignalsResponse {
  repo: string;
  hasPublicRepo: boolean;
  stars: number;
  forks: number;
  openIssues: number;
  lastPushedAt: string;
  velocityClassification: 'HYPER_ACTIVE_DEVELOPMENT' | 'HEALTHY_STEADY_CADENCE' | 'LOW_COMMUNITY_VELOCITY';
  recentReleases: GitHubRelease[];
  techStack: TechStackItem[];
  summary: string;
}

// ============================================================================
// 9. MACHINE LEARNING: ANOMALIES, CLUSTERS & HUGGING FACE
// ============================================================================

export interface AnomalyVector {
  eventCount: number;
  avgImpact: number;
  sentiment: number;
  tierCount: number;
}

export interface MLAnomalyItem {
  date: string;
  index: number;
  anomalyScore: number;
  anomalyType: 'VELOCITY_EXPANSION_ANOMALY' | 'UNUSUAL_STAGNATION_ANOMALY' | 'SENTIMENT_CRISIS_ANOMALY' | 'HIGH_IMPACT_DISRUPTION' | 'STRUCTURAL_MARKET_ANOMALY';
  vector: AnomalyVector;
  description: string;
  severity: 'CRITICAL' | 'HIGH';
}

export interface MLAnomalyResponse {
  competitorName: string;
  hasAnomalies: boolean;
  isLatestPeriodAnomalous: boolean;
  totalObservationsAnalyzed: number;
  totalAnomaliesDetected: number;
  anomalies: MLAnomalyItem[];
  modelMetadata: {
    algorithm: string;
    n_estimators: number;
    contamination: number;
    features: string[];
  };
  summary: string;
}

export interface TopicClusterItem {
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
}

export interface MLTopicClustersResponse {
  totalDocumentsClustered: number;
  kClusters: number;
  algorithm: string;
  dominantTheme: string;
  clusters: TopicClusterItem[];
  summary: string;
}

export interface SemanticSimilarityPayload {
  source_text: string;
  candidate_texts: string[];
}

export interface SemanticSimilarityResponse {
  source_text: string;
  model: string;
  ranking: Array<{
    candidate: string;
    similarity_score: number;
    rank: number;
  }>;
}

export interface BusinessSentimentPayload {
  text: string;
}

export interface BusinessSentimentResponse {
  text: string;
  model: string;
  top_sentiment: 'positive' | 'negative' | 'neutral';
  confidence: number;
  scores: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

// ============================================================================
// 10. AUTONOMOUS GTM ACTION DISPATCH
// ============================================================================

export interface PlaybookRequestPayload {
  competitor_id: string;
  event_context?: Record<string, any> | null;
}

export interface DepartmentalPlaybookResponse {
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
  custom_webhook_url?: string | null;
}

// ============================================================================
// 11. INTELLIGENCE MONITORING & TRENDS
// ============================================================================

export interface IntelligenceDocumentOut {
  id: string;
  competitorId: string;
  competitorName?: string | null;
  sourceUrl: string;
  title?: string | null;
  summary?: string | null;
  eventType?: string | null;
  sentiment?: string | null;
  sentimentConfidence?: number | null;
  relevanceScore?: number | null;
  relevanceReason?: string | null;
  impactScore?: number | null;
  impactLabel?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | null;
  publishedDate?: string | null;
  createdAt?: string | null;
}

export interface IntelligenceFeedResponse {
  documents: IntelligenceDocumentOut[];
  total: number;
  hasMore: boolean;
}

export interface IntelligenceSummaryResponse {
  weeklyBrief?: string | null;
  topThreats: Array<{
    threat: string;
    competitor: string;
    urgency: 'HIGH' | 'MEDIUM' | 'LOW';
    evidence: string;
    recommendedAction: string;
  }>;
  opportunities: Array<{
    opportunity: string;
    basis: string;
    potentialImpact: string;
    recommendedAction: string;
  }>;
  watchList: string[];
  strategicRecommendations: Array<{
    area: string;
    action: string;
    rationale: string;
    expectedOutcome: string;
  }>;
  competitiveVelocity: Array<{
    competitor: string;
    eventCount: number;
    trend: string;
  }>;
  generatedAt?: string | null;
}

export interface CompetitorStats {
  competitorId: string;
  competitorName: string;
  documentCount: number;
  latestEvent?: string | null;
  latestEventDate?: string | null;
}

export interface EventTypeStats {
  eventType: string;
  count: number;
}

export interface IntelligenceStatsResponse {
  totalDocuments: number;
  documentsThisWeek: number;
  criticalEvents: number;
  highEvents: number;
  mediumEvents: number;
  lowEvents: number;
  byCompetitor: CompetitorStats[];
  byEventType: EventTypeStats[];
}

export interface MonitoringJobOut {
  id: string;
  jobType: string;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED';
  progress: number;
  currentStep: string;
  documentsFound: number;
  documentsProcessed: number;
  startedAt?: string | null;
  completedAt?: string | null;
  error?: string | null;
}

export interface MonitoringJobsResponse {
  jobs: MonitoringJobOut[];
}

// ============================================================================
// 12. TASKS & ACTION CENTER KANBAN
// ============================================================================

export interface TaskOut {
  id: string;
  title: string;
  description?: string | null;
  recommendedSteps?: string | null;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'TODO' | 'IN_PROGRESS' | 'DONE' | 'DISMISSED';
  category?: string | null;
  sourceType: 'AI_RECOMMENDED' | 'MANUAL';
  competitorId?: string | null;
  competitorName?: string | null;
  eventType?: string | null;
  impactScore?: number | null;
  jiraIssueUrl?: string | null;
  dueDate?: string | null;
  completedAt?: string | null;
  dismissedAt?: string | null;
  dismissedReason?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface TasksResponse {
  tasks: TaskOut[];
  total: number;
  todo: number;
  inProgress: number;
  done: number;
  dismissed: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface TaskCreatePayload {
  title: string;
  description?: string | null;
  recommendedSteps?: string | null;
  priority?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  category?: string;
  competitorId?: string | null;
  dueDate?: string | null;
}

export interface TaskUpdatePayload {
  title?: string | null;
  description?: string | null;
  recommendedSteps?: string | null;
  priority?: string | null;
  status?: string | null;
  category?: string | null;
  dueDate?: string | null;
  jiraIssueUrl?: string | null;
}

export interface TaskStatusUpdatePayload {
  status: 'TODO' | 'IN_PROGRESS' | 'DONE' | 'DISMISSED';
  dismissedReason?: string | null;
}
```

---

## 3. Page-by-Page Architecture & UI Integration Guide

### Page 1: Authentication & Company Onboarding
* **Target Routes:** `/auth/login`, `/auth/signup`, `/onboarding`
* **Workflow:**
  1. User authenticates via `POST /api/auth/signup` or `POST /api/auth/login`. Frontend saves `access_token` to `localStorage` or Secure Cookies.
  2. Frontend checks onboarding status via `GET /api/company/profile`.
  3. If not completed, frontend displays the onboarding multi-step form and posts to `POST /api/company/profile` with `CompanyProfilePayload`.
  4. The backend immediately queues competitor discovery in the background and sets `setup_status = 'PROCESSING'`.
  5. Frontend polls `GET /api/company/setup-status` every 3 seconds until `status === 'COMPLETED'`.
  6. Upon completion, redirects to `/competitors/review` (Page 2).

---

### Page 2: Competitor Discovery & Review Center
* **Target Route:** `/competitors/review` or `/competitors`
* **Data Fetching:**
  - `GET /api/competitors?status=active&accepted=pending` (Fetch recommended rivals pending decision)
  - `GET /api/competitors?status=active&accepted=true` (Fetch accepted competitors)
* **Actions:**
  - **Accept Competitor:** `POST /api/competitors/{competitor_id}/accept`
  - **Reject Competitor:** `POST /api/competitors/{competitor_id}/reject`
  - **Add Manual Competitor:** `POST /api/competitors/manual` (Body: `{ name, website }`)
  - **Re-trigger AI Discovery:** `POST /api/company/rediscovery`
  - **Trigger Deep Research on Rival:** `POST /api/competitors/{competitor_id}/research`

---

### Page 3: Executive Boardroom & Strategic Brief
* **Target Route:** `/boardroom` or `/dashboard`
* **Data Fetching:**
  - `GET /api/intelligence/strategy-brief` (Returns weekly brief, top threats, opportunities, and velocity trends)
  - `GET /api/competitors/share-of-voice` (Returns market presence tiers and category buzz leader)
* **One-Click Multi-Page Boardroom PDF Export:**
  - Call `GET /api/reports/boardroom-pdf`.
  - The endpoint streams an institutional-grade PDF (`application/pdf`) generated via ReportLab with executive typography and mathematical metrics.
  ```typescript
  export async function downloadBoardroomReport() {
    const res = await fetch('https://ai-backend-zfq1.onrender.com/api/reports/boardroom-pdf', {
      headers: { Authorization: `Bearer ${getAuthToken()}` }
    });
    if (!res.ok) throw new Error('PDF generation failed');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `AURA_Executive_Boardroom_Report.pdf`;
    link.click();
    window.URL.revokeObjectURL(url);
  }
  ```

---

### Page 4: Tactical Sales Battlecard & Deep Signals
* **Target Route:** `/competitors/:competitor_id`
* **Data Sources (Load in parallel via `Promise.all`):**
  1. `GET /api/competitors/{competitor_id}/battlecard`:
     - Live counter-positioning script
     - 3 Landmines to lay in commercial demos
     - Quick dismissals and common objection handlers
     - Win/loss historical performance
  2. `GET /api/competitors/{competitor_id}/signals`:
     - Flagship product extraction & confidence score
     - Pricing Minima ($P_{\min}$) and Maxima ($P_{\max}$)
     - Whitespace tier gap detection
     - Activity peaks (maxima) and sentiment troughs (minima)
  3. `GET /api/competitors/{competitor_id}/community-signals`:
     - Live Reddit and Hacker News voice of customer
     - Net sentiment score (-1.0 to +1.0)
     - Top customer complaints and sample churn quotes
  4. `GET /api/competitors/{competitor_id}/github-signals`:
     - Technical release velocity classification
     - Stars, forks, and open issue velocity
     - Primary programming languages stack breakdown

---

### Page 5: Category Pricing Matrix & Whitespace Explorer
* **Target Route:** `/pricing-matrix`
* **Data Fetching:**
  - `GET /api/competitors/pricing-matrix`
  - `GET /api/competitors/{competitor_id}/deltas` (For historical step-function price changes)
* **UI Visualization:**
  - **Category Benchmark Cards:** Display Market Floor ($P_{\min}$), Market Ceiling ($P_{\max}$), and Category Median.
  - **Tier Comparison Table:** Columns for Free Tier, Starter, Pro, and Enterprise across all active rivals.
  - **Whitespace Gap Callout:** Highlights unoccupied pricing zones (e.g., "$150 - $450 void where no rival offers self-serve").

---

### Page 6: 2D Spatial Positioning Radar
* **Target Route:** `/positioning-radar`
* **Data Fetching:**
  - `GET /api/competitors/positioning-radar`
* **UI Visualization (2D Scatter / Bubble Chart):**
  - **X-Axis (0 to 100):** Market Tier & Price Index (Low to Enterprise).
  - **Y-Axis (0 to 100):** Product Scope & Platform Breadth (Point Tool to Comprehensive Suite).
  - **4 Quadrants:**
    - Top-Right: `ENTERPRISE_PLATFORM`
    - Top-Left: `PREMIUM_SPECIALIST`
    - Bottom-Right: `DISRUPTIVE_CHALLENGER`
    - Bottom-Left: `LIGHTWEIGHT_POINT_SOLUTION`
  - **Threat Radar Lines:** Draw dotted alert lines to competitors with Euclidean Distance $< 25.0$ (`CRITICAL_ENCROACHMENT`).

---

### Page 7: Commercial Win/Loss Deal Intelligence
* **Target Route:** `/deals`
* **Data Fetching:**
  - `GET /api/deals/analytics` (Overall win rate %, pipeline won vs lost, loss reason distribution)
* **Interactions:**
  - **"Record Deal Outcome" Modal:** Submits to `POST /api/deals/outcome` with `DealOutcomePayload`.
  - **Head-to-Head Win Rate Chart:** Displays individual win rates against each rival with primary loss factors.

---

### Page 8: Machine Learning & NLP Topic Lab
* **Target Route:** `/ml-lab`
* **Data Fetching & Submissions:**
  - `GET /api/competitors/{competitor_id}/ml-anomalies` (IsolationForest statistical anomaly spikes)
  - `GET /api/intelligence/ml-clusters?num_clusters=4` (KMeans thematic clustering of market events)
  - `POST /api/ml/semantic-similarity` (Hugging Face MiniLM dense semantic ranking)
  - `POST /api/ml/business-sentiment` (Hugging Face FinBERT financial and corporate sentiment)

---

### Page 9: Autonomous Action Center & Tasks Kanban
* **Target Route:** `/actions` or `/tasks`
* **Features:**
  1. **Kanban Columns (`TODO`, `IN_PROGRESS`, `DONE`, `DISMISSED`):**
     - Fetch tasks via `GET /api/tasks?status=active`.
     - Drag-and-drop triggers `POST /api/tasks/{task_id}/status` with `{ "status": "IN_PROGRESS" }`.
  2. **Playbook Generator:**
     - Calls `POST /api/actions/playbook` with `{ "competitor_id": id }`.
     - Generates 4 direct department directives (Product Jira ticket, Sales counter script, Marketing campaign, Executive decision).
  3. **Direct Jira Cloud REST Dispatch:**
     - Form calls `POST /api/actions/jira` to instantly create a ticket in Atlassian Jira Cloud.
  4. **Instant WhatsApp / Mobile Webhook Alert:**
     - Dispatches formatted alert via `POST /api/actions/whatsapp`.

---

### Page 10: Live Intelligence Feed, Trends & Monitoring Jobs
* **Target Route:** `/intelligence-feed`
* **Data Fetching:**
  - `GET /api/intelligence/feed?limit=20&offset=0` (Paginated event stream)
  - `GET /api/intelligence/trends` (Weekly event trends & momentum)
  - `GET /api/intelligence/alerts` (Urgent market alerts)
  - `POST /api/intelligence/check-now` (Manual trigger for news monitor)
  - `GET /api/intelligence/check-status` (Polls manual check progress)
  - `GET /api/intelligence/jobs` (Monitoring jobs history log)

---

## 4. Master 52-Endpoint API Reference Table

| # | Method | Full URL Path | Description | Key Params / Request Body |
|---|:---:|---|---|---|
| **1** | `GET` | `/` | Service health check | None |
| **2** | `POST` | `/analyze` | Run full Jina Reader AI deep research pipeline | Body: `CompetitorRequest` |
| **3** | `POST` | `/api/auth/signup` | Register new user via Supabase | Body: `AuthRequest` |
| **4** | `POST` | `/api/auth/login` | Login user and retrieve JWT | Body: `AuthRequest` |
| **5** | `GET` | `/api/company/profile` | Get company onboarding profile & brief | Auth Header |
| **6** | `POST` | `/api/company/profile` | Submit company profile & trigger discovery | Body: `CompanyProfilePayload` |
| **7** | `PUT` | `/api/company/profile` | Partially update company profile details | Body: `CompanyProfileUpdatePayload` |
| **8** | `GET` | `/api/company/setup-status` | Poll onboarding & discovery progress % | Auth Header |
| **9** | `POST` | `/api/company/trigger-discovery` | Retry / Trigger competitor discovery | Auth Header |
| **10** | `POST` | `/api/company/rediscovery` | Rate-limited re-discovery trigger | Auth Header |
| **11** | `GET` | `/api/company/settings` | Get company CI configuration | Auth Header |
| **12** | `PUT` | `/api/company/settings` | Update company CI preferences | Body: `CompanySettingsUpdatePayload` |
| **13** | `GET` | `/api/company/activity` | Audit log trail of actions | Query: `limit`, `offset` |
| **14** | `GET` | `/api/competitors` | List competitors with filters | Query: `status`, `type`, `accepted` |
| **15** | `POST` | `/api/competitors/manual` | Add manual competitor immediately | Body: `ManualCompetitorRequest` |
| **16** | `PUT` | `/api/competitors/{competitor_id}` | Edit competitor name, type, or notes | Body: `CompetitorEditPayload` |
| **17** | `DELETE`| `/api/competitors/{competitor_id}` | Permanently delete competitor | Path: `competitor_id` |
| **18** | `POST` | `/api/competitors/{competitor_id}/archive` | Archive competitor from active pool | Path: `competitor_id` |
| **19** | `POST` | `/api/competitors/{competitor_id}/restore` | Restore archived competitor | Path: `competitor_id` |
| **20** | `POST` | `/api/competitors/{competitor_id}/research` | Run deep AI re-research background job | Path: `competitor_id` |
| **21** | `POST` | `/api/competitors/{competitor_id}/accept` | Accept rival recommendation into monitor | Path: `competitor_id` |
| **22** | `POST` | `/api/competitors/{competitor_id}/reject` | Reject/dismiss rival recommendation | Path: `competitor_id` |
| **23** | `GET` | `/api/competitors/{competitor_id}/battlecard` | 1-page tactical sales battlecard | Path: `competitor_id` |
| **24** | `GET` | `/api/competitors/{competitor_id}/signals` | Flagship product, Price Min/Max, Peaks | Path: `competitor_id` |
| **25** | `GET` | `/api/competitors/pricing-matrix` | Category pricing benchmarks & whitespace | Auth Header |
| **26** | `GET` | `/api/competitors/{competitor_id}/snapshots` | Historical state snapshot history | Path: `competitor_id` |
| **27** | `GET` | `/api/competitors/{competitor_id}/deltas` | Step-function price & messaging shifts | Path: `competitor_id` |
| **28** | `GET` | `/api/competitors/positioning-radar` | 2D coordinates, quadrants & encroachment | Auth Header |
| **29** | `POST` | `/api/deals/outcome` | Record a commercial deal result | Body: `DealOutcomePayload` |
| **30** | `GET` | `/api/deals/analytics` | Win rates, revenue lost & loss reasons | Auth Header |
| **31** | `GET` | `/api/competitors/{competitor_id}/community-signals`| Live Reddit & Hacker News customer voice | Path: `competitor_id` |
| **32** | `GET` | `/api/reports/boardroom-pdf` | Downloadable executive boardroom PDF | Streams `application/pdf` |
| **33** | `GET` | `/api/competitors/share-of-voice` | Category Share of Voice % rankings | Auth Header |
| **34** | `GET` | `/api/competitors/{competitor_id}/github-signals` | Open-source release cadence & tech stack | Path: `competitor_id` |
| **35** | `GET` | `/api/competitors/{competitor_id}/ml-anomalies` | IsolationForest statistical anomaly flags | Path: `competitor_id` |
| **36** | `GET` | `/api/intelligence/ml-clusters` | KMeans ($k=3..5$) thematic clusters | Query: `num_clusters` |
| **37** | `POST` | `/api/ml/semantic-similarity` | Hugging Face dense semantic similarity | Body: `SemanticSimilarityPayload` |
| **38** | `POST` | `/api/ml/business-sentiment` | Hugging Face FinBERT business sentiment | Body: `BusinessSentimentPayload` |
| **39** | `POST` | `/api/actions/playbook` | Generate 4-department tactical playbook | Body: `PlaybookRequestPayload` |
| **40** | `POST` | `/api/actions/jira` | Directly create ticket in Jira Cloud REST | Body: `JiraCreatePayload` |
| **41** | `POST` | `/api/actions/whatsapp` | Dispatch WhatsApp / Webhook alert | Body: `WhatsAppAlertPayload` |
| **42** | `GET` | `/api/intelligence/feed` | Filtered intelligence news & event stream | Query: `limit`, `offset`, `eventType` |
| **43** | `GET` | `/api/intelligence/strategy-brief` | Weekly brief, threats & recommendations | Auth Header |
| **44** | `GET` | `/api/intelligence/competitor-stats` | Document counts & latest events by rival | Auth Header |
| **45** | `GET` | `/api/intelligence/trends` | Event trends & momentum classifications | Auth Header |
| **46** | `GET` | `/api/intelligence/alerts` | Critical high-severity market alerts | Auth Header |
| **47** | `POST` | `/api/intelligence/trigger-monitoring` | Trigger background news crawler | Auth Header |
| **48** | `POST` | `/api/intelligence/generate-summary` | Manually regenerate Strategy Brief | Auth Header |
| **49** | `GET` | `/api/intelligence/jobs` | Background monitoring jobs log | Auth Header |
| **50** | `POST` | `/api/intelligence/check-now` | Trigger foreground manual monitor check | Auth Header |
| **51** | `GET` | `/api/intelligence/check-status` | Check status of active manual monitor check | Auth Header |
| **52** | `GET` | `/api/tasks` | Action center Kanban tasks list & stats | Query: `status`, `priority` |

---

## 5. Frontend Error Handling & Client Setup

Below is a production-ready Axios client instance configured for the live Render environment:

```typescript
// src/api/client.ts
import axios from 'axios';

export const API_BASE_URL = 'https://ai-backend-zfq1.onrender.com';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000, // 45 seconds for deep ML/scraping requests
});

// Attach Supabase Bearer Token dynamically
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('supabase_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Centralized Error Interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login if token is expired
      window.location.href = '/auth/login';
    }
    const message = error.response?.data?.detail || error.message || 'Unknown network error';
    return Promise.reject(new Error(message));
  }
);
```
