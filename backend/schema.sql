-- =============================================================================
-- AURA-CI: COMPLETE SUPABASE POSTGRESQL SCHEMA MIGRATION
-- Paste this entire script into your Supabase SQL Editor and click "Run".
-- Safe & Non-Destructive: Uses IF NOT EXISTS and ADD COLUMN IF NOT EXISTS.
-- =============================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 2. COMPANIES TABLE (Tenant Profiles & Weekly AI Strategy Briefs)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name TEXT NOT NULL,
    industry TEXT,
    website_url TEXT,
    description TEXT,
    products_or_services TEXT,
    owner_id TEXT,
    setup_status TEXT DEFAULT 'PENDING',
    setup_current_step INT DEFAULT 1,
    weekly_brief TEXT,
    weekly_brief_generated_at TIMESTAMPTZ,
    top_threats JSONB DEFAULT '[]'::jsonb,
    opportunities JSONB DEFAULT '[]'::jsonb,
    strategic_recommendations JSONB DEFAULT '[]'::jsonb,
    competitive_velocity TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure newly added columns exist in case companies already exists
ALTER TABLE public.companies ADD COLUMN IF NOT EXISTS owner_id TEXT;
ALTER TABLE public.companies ADD COLUMN IF NOT EXISTS setup_status TEXT DEFAULT 'PENDING';
ALTER TABLE public.companies ADD COLUMN IF NOT EXISTS setup_current_step INT DEFAULT 1;
ALTER TABLE public.companies ADD COLUMN IF NOT EXISTS weekly_brief TEXT;
ALTER TABLE public.companies ADD COLUMN IF NOT EXISTS weekly_brief_generated_at TIMESTAMPTZ;
ALTER TABLE public.companies ADD COLUMN IF NOT EXISTS top_threats JSONB DEFAULT '[]'::jsonb;
ALTER TABLE public.companies ADD COLUMN IF NOT EXISTS opportunities JSONB DEFAULT '[]'::jsonb;
ALTER TABLE public.companies ADD COLUMN IF NOT EXISTS strategic_recommendations JSONB DEFAULT '[]'::jsonb;
ALTER TABLE public.companies ADD COLUMN IF NOT EXISTS competitive_velocity TEXT;
ALTER TABLE public.companies ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- =============================================================================
-- 3. COMPETITORS TABLE (Tracked Market Rivals & AI Scoring)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.competitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES public.companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    website_url TEXT,
    description TEXT,
    industry TEXT,
    competitive_score NUMERIC DEFAULT 50.0,
    confidence_score NUMERIC DEFAULT 50.0,
    market_overlap NUMERIC DEFAULT 50.0,
    product_similarity NUMERIC DEFAULT 50.0,
    business_model_overlap NUMERIC DEFAULT 50.0,
    customer_overlap NUMERIC DEFAULT 50.0,
    is_accepted BOOLEAN DEFAULT FALSE,
    action TEXT DEFAULT 'PENDING',
    reason TEXT,
    research_status TEXT DEFAULT 'IDLE',
    executive_summary TEXT,
    social_urls JSONB DEFAULT '{}'::jsonb,
    focus_areas JSONB DEFAULT '[]'::jsonb,
    competitor_snapshot JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure newly added columns exist
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS competitive_score NUMERIC DEFAULT 50.0;
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS confidence_score NUMERIC DEFAULT 50.0;
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS market_overlap NUMERIC DEFAULT 50.0;
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS product_similarity NUMERIC DEFAULT 50.0;
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS business_model_overlap NUMERIC DEFAULT 50.0;
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS customer_overlap NUMERIC DEFAULT 50.0;
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS is_accepted BOOLEAN DEFAULT FALSE;
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS action TEXT DEFAULT 'PENDING';
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS reason TEXT;
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS research_status TEXT DEFAULT 'IDLE';
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS executive_summary TEXT;
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS social_urls JSONB DEFAULT '{}'::jsonb;
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS focus_areas JSONB DEFAULT '[]'::jsonb;
ALTER TABLE public.competitors ADD COLUMN IF NOT EXISTS competitor_snapshot JSONB DEFAULT '{}'::jsonb;

-- =============================================================================
-- 4. COMPETITOR SNAPSHOTS TABLE (Historical Time-Series & Pricing Shifts)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.competitor_snapshots (
    id TEXT PRIMARY KEY,
    company_id TEXT,
    competitor_id TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    flagship_product TEXT,
    price_minima NUMERIC,
    price_maxima NUMERIC,
    price_median NUMERIC,
    pricing_tiers JSONB DEFAULT '[]'::jsonb,
    event_count INT DEFAULT 0,
    sentiment_score NUMERIC DEFAULT 0.0,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 5. DEAL OUTCOMES TABLE (Commercial Sales Win/Loss Deal Analytics)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.deal_outcomes (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    competitor_id TEXT NOT NULL,
    competitor_name TEXT,
    outcome TEXT NOT NULL, -- WON, LOST, TIED
    deal_value NUMERIC DEFAULT 0.0,
    primary_reason TEXT DEFAULT 'FEATURE_GAP',
    competitor_strength TEXT,
    prospect_name TEXT,
    notes TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 6. INTELLIGENCE DOCUMENTS & FEED (Scraped Events & News)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.intelligence_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID,
    competitor_id UUID,
    competitor_name TEXT,
    title TEXT NOT NULL,
    source_url TEXT,
    summary TEXT,
    event_type TEXT DEFAULT 'OTHER',
    sub_type TEXT,
    impact_label TEXT DEFAULT 'MEDIUM',
    impact_score NUMERIC DEFAULT 50.0,
    relevance_score NUMERIC DEFAULT 50.0,
    sentiment TEXT DEFAULT 'NEUTRAL',
    sentiment_score NUMERIC DEFAULT 0.0,
    published_date TIMESTAMPTZ,
    extracted_signals JSONB DEFAULT '{}'::jsonb,
    raw_content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure newly added columns exist in intelligence_documents
ALTER TABLE public.intelligence_documents ADD COLUMN IF NOT EXISTS sub_type TEXT;
ALTER TABLE public.intelligence_documents ADD COLUMN IF NOT EXISTS impact_score NUMERIC DEFAULT 50.0;
ALTER TABLE public.intelligence_documents ADD COLUMN IF NOT EXISTS relevance_score NUMERIC DEFAULT 50.0;
ALTER TABLE public.intelligence_documents ADD COLUMN IF NOT EXISTS sentiment_score NUMERIC DEFAULT 0.0;

-- Documents alias table (if used by legacy scraper)
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id UUID,
    company_id UUID,
    competitor_name TEXT,
    title TEXT,
    source_url TEXT,
    summary TEXT,
    event_type TEXT,
    impact_label TEXT,
    published_date TIMESTAMPTZ,
    is_processed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 7. MONITORING JOBS & URL CACHE (Background Scraper Execution Tracking)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.monitoring_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID,
    status TEXT DEFAULT 'RUNNING',
    documents_found INT DEFAULT 0,
    documents_processed INT DEFAULT 0,
    error TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.url_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID,
    competitor_id UUID,
    url TEXT UNIQUE NOT NULL,
    content_hash TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 8. TASKS & AUDIT LOGS (GTM Workflows & System Activity Logs)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, CRITICAL
    category TEXT DEFAULT 'GENERAL',
    status TEXT DEFAULT 'TODO', -- TODO, IN_PROGRESS, DONE, DISMISSED
    competitor_id UUID,
    competitor_name TEXT,
    source_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    action TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 9. HIGH-PERFORMANCE QUERY INDEXES
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_competitors_company ON public.competitors(company_id);
CREATE INDEX IF NOT EXISTS idx_competitors_accepted ON public.competitors(is_accepted);
CREATE INDEX IF NOT EXISTS idx_intel_docs_company ON public.intelligence_documents(company_id);
CREATE INDEX IF NOT EXISTS idx_intel_docs_competitor ON public.intelligence_documents(competitor_id);
CREATE INDEX IF NOT EXISTS idx_intel_docs_impact ON public.intelligence_documents(impact_score DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_comp_date ON public.competitor_snapshots(competitor_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_deals_company ON public.deal_outcomes(company_id);
CREATE INDEX IF NOT EXISTS idx_deals_competitor ON public.deal_outcomes(competitor_id);
CREATE INDEX IF NOT EXISTS idx_tasks_company_status ON public.tasks(company_id, status);

-- =============================================================================
-- 10. ENABLE ROW LEVEL SECURITY (RLS) & PUBLIC ACCESS POLICIES
-- =============================================================================
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.competitors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.competitor_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.deal_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.intelligence_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;

-- Allow backend service role & public client read/write
DO $$
BEGIN
    DROP POLICY IF EXISTS "Public Full Access Companies" ON public.companies;
    CREATE POLICY "Public Full Access Companies" ON public.companies FOR ALL USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "Public Full Access Competitors" ON public.competitors;
    CREATE POLICY "Public Full Access Competitors" ON public.competitors FOR ALL USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "Public Full Access Snapshots" ON public.competitor_snapshots;
    CREATE POLICY "Public Full Access Snapshots" ON public.competitor_snapshots FOR ALL USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "Public Full Access Deals" ON public.deal_outcomes;
    CREATE POLICY "Public Full Access Deals" ON public.deal_outcomes FOR ALL USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "Public Full Access Intel Docs" ON public.intelligence_documents;
    CREATE POLICY "Public Full Access Intel Docs" ON public.intelligence_documents FOR ALL USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "Public Full Access Tasks" ON public.tasks;
    CREATE POLICY "Public Full Access Tasks" ON public.tasks FOR ALL USING (true) WITH CHECK (true);
END $$;
