"""
Pydantic models for Competitor Analysis AI.

Defines the request schema (CompetitorRequest), intermediate data structures
(DataPoint), and the full response schema (CompetitorReport).
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, HttpUrl, Field


class CompetitorRequest(BaseModel):
    """Incoming request payload for competitor analysis."""

    company_name: str = Field(..., description="Name of the competitor company to analyze.")
    website_url: HttpUrl = Field(..., description="Primary website URL of the competitor.")
    industry: str = Field(..., description="Industry or vertical the competitor operates in.")
    our_company_context: str = Field(
        default="We are a similar business competing in the same market.",
        description="Brief description of our own company for contextual analysis.",
    )
    social_urls: dict[str, str] = Field(
        default_factory=dict,
        description="Optional mapping of platform name to social profile URL.",
    )
    focus_areas: list[str] = Field(
        default=["products", "pricing", "positioning", "social", "seo"],
        description="Aspects of the competitor to focus the analysis on.",
    )


class DataPoint(BaseModel):
    """A single extracted data point from scraped content."""

    category: str = Field(..., description="Category of the data point (e.g., 'pricing', 'product').")
    key: str = Field(..., description="Specific attribute name.")
    value: str = Field(..., description="Extracted value.")
    source: str = Field(..., description="URL or source the data was extracted from.")
    confidence: str = Field(..., description="Confidence level: high, medium, or low.")


class CompetitorReport(BaseModel):
    """Full competitor intelligence report returned by the API."""

    company_name: str
    executive_summary: str
    snapshot: dict[str, str]
    strengths: list[str]
    weaknesses: list[str]
    opportunities: list[str]
    threats: list[str]
    swot: dict[str, list[str]]
    next_steps: list[dict[str, Any]]
    differentiation_strategy: str
    full_markdown_report: str
    generated_at: datetime


# --- Onboarding Models ---

class CompetitorManual(BaseModel):
    """A manual competitor entry provided by the user."""
    name: str
    website: Optional[str] = None

class CompanyProfilePayload(BaseModel):
    """Payload for submitting or updating a company profile."""
    companyName: str = Field(..., description="Name of the company")
    website: HttpUrl = Field(..., description="Company website URL")
    industry: str = Field(..., description="Industry the company operates in")
    description: str = Field(..., description="Description of the company")
    productsOrServices: list[str] = Field(..., description="List of products or services")
    targetCustomers: str = Field(..., description="Information about target customers or market")
    
    companyStage: Optional[str] = Field(None, description="Current stage of the company")
    companySize: Optional[str] = Field(None, description="Size of the company")
    competitors: Optional[list[CompetitorManual]] = Field(None, description="List of known competitors")
    excludedCompetitors: Optional[list[str]] = Field(None, description="Competitors to exclude from analysis")

class CompanyProfileUpdatePayload(BaseModel):
    """Payload for updating an existing company profile."""
    companyName: Optional[str] = Field(None, min_length=2, max_length=100)
    website: Optional[HttpUrl] = None
    industry: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    companyStage: Optional[str] = None
    companySize: Optional[str] = None
    businessType: Optional[str] = None
    customerSegments: Optional[list[str]] = None
    geographicMarkets: Optional[list[str]] = None
    productsOrServices: Optional[str] = None
    primaryProblemSolved: Optional[str] = None

class CompanySettingsOut(BaseModel):
    monitoringEnabled: bool
    emailDigestEnabled: bool
    criticalAlertsEnabled: bool
    maxCompetitorsMonitored: int
    discoveryRunCount: int
    lastDiscoveryAt: Optional[str] = None
    activeCompetitors: int
    archivedCompetitors: int

class CompanySettingsUpdatePayload(BaseModel):
    monitoringEnabled: Optional[bool] = None
    emailDigestEnabled: Optional[bool] = None
    criticalAlertsEnabled: Optional[bool] = None
    maxCompetitorsMonitored: Optional[int] = Field(None, ge=1, le=25)

class AuditLogOut(BaseModel):
    id: str
    action: str
    entityType: str
    entityId: str
    metadata: dict[str, Any] = {}
    createdAt: str

class AuditLogResponse(BaseModel):
    activities: list[AuditLogOut]
    total: int

class CompanyProfileResponseCompany(BaseModel):
    id: str
    companyName: str
    website: str
    industry: str
    setupStatus: Optional[str] = None
    executiveBrief: Optional[str] = None
    mainThreats: Optional[list[str]] = None
    keyOpportunity: Optional[str] = None

class CompanyProfileResponse(BaseModel):
    """Response showing if setup is complete, and basic company details if so."""
    setupCompleted: bool
    company: Optional[CompanyProfileResponseCompany] = None


# --- Auth Models ---

class AuthRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


# --- Discovery Pipeline Models ---

class SetupStatusResponse(BaseModel):
    """Response for GET /api/company/setup-status."""
    status: str
    progress: int
    currentStep: Optional[str] = None
    completedAt: Optional[str] = None
    error: Optional[str] = None


class CompetitorOut(BaseModel):
    """Serialised competitor row returned by the API."""
    id: str
    name: str
    website: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    source: Optional[str] = None
    competitiveScore: Optional[int] = None
    confidenceScore: Optional[int] = None
    productSimilarity: Optional[int] = None
    customerOverlap: Optional[int] = None
    marketOverlap: Optional[int] = None
    businessModelOverlap: Optional[int] = None
    reason: Optional[str] = None
    isAccepted: Optional[bool] = None
    isActive: Optional[bool] = None
    customType: Optional[str] = None
    effectiveType: Optional[str] = None
    notes: Optional[str] = None
    lastResearchedAt: Optional[str] = None
    researchStatus: Optional[str] = None


class CompetitorsListResponse(BaseModel):
    """Response for GET /api/competitors."""
    competitors: list[CompetitorOut]
    total: int
    active: int
    archived: int
    direct: int
    indirect: int
    emerging: int
    pendingReview: int


class ManualCompetitorRequest(BaseModel):
    """Body for POST /api/competitors/manual."""
    name: str = Field(..., description="Name of the competitor")
    website: str = Field(..., description="Website URL of the competitor")

class CompetitorEditPayload(BaseModel):
    """Body for PUT /api/competitors/{id}"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    website: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)
    customType: Optional[str] = None


# --- Intelligence Monitoring Models ---

class IntelligenceDocumentOut(BaseModel):
    id: str
    competitorId: str
    competitorName: Optional[str] = None
    sourceUrl: str
    title: Optional[str] = None
    summary: Optional[str] = None
    eventType: Optional[str] = None
    sentiment: Optional[str] = None
    sentimentConfidence: Optional[int] = None
    relevanceScore: Optional[int] = None
    relevanceReason: Optional[str] = None
    impactScore: Optional[int] = None
    impactLabel: Optional[str] = None
    publishedDate: Optional[str] = None
    createdAt: Optional[str] = None


class IntelligenceFeedResponse(BaseModel):
    documents: list[IntelligenceDocumentOut]
    total: int
    hasMore: bool


class IntelligenceSummaryResponse(BaseModel):
    weeklyBrief: Optional[str] = None
    topThreats: list[dict[str, Any]] = []
    opportunities: list[dict[str, Any]] = []
    watchList: list[str] = []
    strategicRecommendations: list[str] = []
    generatedAt: Optional[str] = None


class CompetitorStats(BaseModel):
    competitorId: str
    competitorName: str
    documentCount: int
    latestEvent: Optional[str] = None
    latestEventDate: Optional[str] = None


class EventTypeStats(BaseModel):
    eventType: str
    count: int


class IntelligenceStatsResponse(BaseModel):
    totalDocuments: int
    documentsThisWeek: int
    criticalEvents: int
    highEvents: int
    mediumEvents: int
    lowEvents: int
    byCompetitor: list[CompetitorStats]
    byEventType: list[EventTypeStats]


class MonitoringJobOut(BaseModel):
    id: str
    jobType: str
    status: str
    documentsFound: int
    documentsProcessed: int
    startedAt: Optional[str] = None
    completedAt: Optional[str] = None
    error: Optional[str] = None


class MonitoringJobsResponse(BaseModel):
    jobs: list[MonitoringJobOut]

