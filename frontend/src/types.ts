// API TypeScript Types and Interfaces for Competitor Intelligence App

export interface AuthPayload {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  user_id: string;
  email: string;
}

export interface CompanyDetails {
  id: string;
  companyName: string;
  website: string;
  industry: string;
  setupStatus: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  executiveBrief?: string;
  mainThreats?: string[];
  keyOpportunity?: string;
  description?: string;
  productsOrServices?: string[];
  targetCustomers?: string;
  companyStage?: string;
  companySize?: string;
  briefGeneratedAt?: string;
}

export interface CompanyProfileResponse {
  setupCompleted: boolean;
  company: CompanyDetails | null;
}

export interface CompanySubmitPayload {
  companyName: string;
  website: string;
  industry: string;
  description: string;
  productsOrServices: string[];
  targetCustomers: string;
  companyStage: string;
  companySize: string;
}

export interface SetupStatusResponse {
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress: number; // Integer 0 to 100
  currentStep: string;
  completedAt?: string | null;
  error?: string | null;
}

export interface CompetitorItem {
  id: string;
  name: string;
  website?: string;
  description?: string;
  type: 'DIRECT' | 'INDIRECT' | 'EMERGING' | string;
  source: 'AI_DISCOVERED' | 'MANUAL' | string;
  competitiveScore: number | null;
  confidenceScore?: number;
  productSimilarity?: number;
  customerOverlap?: number;
  marketOverlap?: number;
  businessModelOverlap?: number;
  reason?: string;
  isAccepted: boolean | null;
}

export interface CompetitorsResponse {
  total: number;
  direct: number;
  indirect: number;
  emerging: number;
  competitors: CompetitorItem[];
}

export interface ManualCompetitorPayload {
  name: string;
  website: string;
}

// ── Phase 2: Live Competitor Monitoring Types ──

export interface CompetitorStat {
  competitorId: string;
  competitorName: string;
  documentCount: number;
  latestEventType?: string;
}

export interface IntelligenceStats {
  documentsThisWeek: number;
  criticalEvents: number;
  highEvents: number;
  mediumEvents: number;
  lowEvents: number;
  total?: number;
  byCompetitor: CompetitorStat[];
  lastMonitoredCompletedAt?: string | null;
  weeklyBriefGeneratedAt?: string | null;
  monitoredCount?: number;
}

export interface IntelligenceFeedItem {
  id: string;
  title: string;
  summary: string;
  competitorId?: string;
  competitorName: string;
  eventType: string;
  impact: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | string;
  sentiment: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL' | string;
  relevanceScore: number;
  impactScore: number;
  sourceUrl: string;
  publishedAt?: string;
  date?: string;
  relevanceReason?: string;
  eventTypeExplanation?: string;
  additionalContext?: string;
}

export interface IntelligenceFeedResponse {
  total: number;
  documents: IntelligenceFeedItem[];
}

export interface FeedQueryParams {
  competitorId?: string;
  eventType?: string;
  impact?: string;
  limit?: number;
  offset?: number;
}

export interface StrategyThreat {
  urgency: 'HIGH' | 'MEDIUM' | 'LOW' | string;
  description: string;
  competitorName: string;
  recommendedAction: string;
}

export interface StrategyOpportunity {
  description: string;
  basis: string;
  recommendedAction: string;
}

export interface IntelligenceSummaryResponse {
  weeklyBrief: string;
  weeklyBriefGeneratedAt: string;
  topThreats: StrategyThreat[];
  opportunities: StrategyOpportunity[];
  watchList: string[];
  strategicRecommendations: string[];
  // Phase 3 additions:
  criticalAlerts?: AlertItem[];
  trendSummary?: string;
  anomalySummary?: string;
}

// ── Phase 3: Trends, Anomalies, and Alerts Types ──

export interface AlertItem {
  id: string;
  type: 'TREND' | 'ANOMALY' | string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | string;
  urgency: 'ACT_NOW' | 'MONITOR' | 'WATCH' | string;
  title: string;
  description: string;
  competitorId: string;
  competitorName: string;
  detectedAt: string;
  isAcknowledged: boolean;
  acknowledgedAt?: string;
  recommendedAction?: string;
}

export interface AlertsResponse {
  totalUnacknowledged: number;
  criticalUnacknowledged: number;
  highUnacknowledged: number;
  mediumUnacknowledged: number;
  lowUnacknowledged: number;
  alerts: AlertItem[];
}

export interface TrendItem {
  id: string;
  trendType: 'ACTIVITY_SPIKE' | 'ACTIVITY_DECLINE' | 'SENTIMENT_SHIFT_POSITIVE' | 'SENTIMENT_SHIFT_NEGATIVE' | 'EVENT_CLUSTER' | 'HIRING_SURGE' | 'PRODUCT_ACCELERATION' | 'MARKET_EXPANSION' | string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | string;
  description: string;
  competitorId: string;
  competitorName: string;
  changePercent: number;
  currentValue: number;
  baselineValue: number;
  periodStart: string;
  periodEnd: string;
  strategicImplication?: string;
  recommendedAction?: string;
  isActive: boolean;
}

export interface TrendsResponse {
  totalActive: number;
  criticalCount: number;
  highCount: number;
  trendingCompetitorsCount: number;
  trends: TrendItem[];
}

export interface MetricDataPoint {
  date: string; // ISO date string (YYYY-MM-DD)
  documentCount: number;
  criticalCount: number;
  highCount: number;
  positiveSentimentCount: number;
  negativeSentimentCount: number;
  neutralSentimentCount: number;
  eventTypeCounts: Record<string, number>;
}

export interface MetricsResponse {
  competitorId: string;
  days: number;
  totalDocuments: number;
  averageDailyActivity: number;
  peakDay: string;
  peakDayCount: number;
  timeseries: MetricDataPoint[];
}
