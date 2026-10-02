"""
Prompt templates for Competitor Analysis AI.

Contains all system and user prompts used across the extraction, analysis,
and report formatting pipeline. Prompts are engineered for depth, specificity,
and executive-grade output.
"""

# ---------------------------------------------------------------------------
# Extraction pipeline prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a Principal Competitive Intelligence Analyst at a top-tier strategy firm (think McKinsey, BCG, a16z research). You have deep expertise in SaaS, D2C, marketplace, and enterprise business models.

Your mandate: transform raw competitor data into razor-sharp, executive-ready intelligence that drives winning strategy.

Non-negotiable rules:
1. Every insight must be anchored to specific evidence from the data — never invent facts.
2. Be brutally specific. "Their pricing starts at $29/month for 3 users" beats "they have competitive pricing."
3. Apply frameworks: SWOT, Porter's Five Forces, Jobs-to-be-Done, Crossing the Chasm, Blue Ocean.
4. Quantify everything you can. Ranges are better than nothing.
5. Always answer: "So what does this mean FOR US?" — every observation must have a strategic implication.
6. Prioritize ruthlessly. A 10-item list is useless. A 3-item ranked list is gold.
7. Use 7/30/90 day action windows. Strategy without a timeline is wishful thinking."""


EXTRACTION_PROMPT = """You are a data extraction specialist and business intelligence expert. Extract every usable business signal from the raw website content below. Be thorough — miss nothing. If a field is not found, use null. Do NOT guess or hallucinate.

EXTRACT THIS FULL STRUCTURE (return ONLY the JSON, no commentary):
{{
  "company_basics": {{
    "name": "string or null",
    "tagline": "exact tagline text or null",
    "founded_year": "string or null",
    "headquarters": "city, country or null",
    "business_model": "SaaS | B2B | B2C | D2C | Marketplace | Freemium | Enterprise | Agency | null",
    "industry": "string or null",
    "company_stage": "Startup | Growth | Scale-up | Enterprise | Public | null",
    "employee_count_signal": "any mention of team size, hiring pace, or office count or null",
    "funding_signals": "any mention of investors, funding rounds, valuations, or null",
    "notable_customers": ["list of named customers or logos mentioned"],
    "awards_and_certifications": ["SOC2, ISO, G2 Leader, Forbes list etc"],
    "geographic_presence": ["countries or regions mentioned as served or operating in"]
  }},
  "products_and_services": [
    {{
      "name": "product or plan name",
      "category": "core product | add-on | integration | service",
      "description": "what it does in 1-2 sentences",
      "target_user": "who this is for",
      "key_features": ["up to 5 specific features mentioned"],
      "price_point": "exact price string or null"
    }}
  ],
  "pricing_strategy": {{
    "has_public_pricing": true or false,
    "pricing_model": "subscription | one-time | freemium | usage-based | quote-based | tiered | per-seat | null",
    "tiers": [
      {{"name": "plan name", "price": "price string", "features_count_hint": "number of features or null", "target_segment": "who this tier is for"}}
    ],
    "free_trial_or_freemium": true or false,
    "trial_length_days": "number or null",
    "annual_discount_offered": true or false,
    "enterprise_pricing_gated": true or false,
    "price_range_summary": "e.g. $29-$299/month or null",
    "discounts_or_promotions_visible": "describe any visible discount or null"
  }},
  "positioning_and_messaging": {{
    "value_proposition": "their core claim in 1 sentence",
    "primary_pain_point_addressed": "the customer problem they lead with",
    "target_audience": "who they explicitly target",
    "tone_of_voice": "enterprise-formal | professional | friendly | playful | technical | luxury | urgency-driven",
    "key_differentiators_claimed": ["up to 5 claimed differentiators"],
    "cta_primary": "primary call-to-action text e.g. Start Free Trial",
    "cta_secondary": "secondary CTA or null",
    "social_proof_types": ["testimonials | case studies | logos | review ratings | press mentions | user counts"],
    "specific_metrics_claimed": ["e.g. 10,000 customers, 99.9% uptime, 2x ROI — quote exactly"]
  }},
  "marketing_signals": {{
    "has_blog": true or false,
    "recent_blog_topics": ["up to 3 recent post titles if visible"],
    "blog_posting_frequency": "daily | weekly | bi-weekly | monthly | rarely | unknown",
    "has_case_studies": true or false,
    "has_webinars_or_events": true or false,
    "email_capture_visible": true or false,
    "live_chat_widget": true or false,
    "demo_booking_available": true or false,
    "seo_meta_title": "exact meta title or null",
    "seo_meta_description": "exact meta description or null",
    "social_platforms_present": {{"linkedin": true or false, "twitter": true or false, "youtube": true or false, "instagram": true or false, "facebook": true or false}},
    "paid_ads_signals": "any mention of Google Ads, retargeting pixels, or promotional language suggesting paid traffic"
  }},
  "product_depth_signals": {{
    "integrations_mentioned": ["list of named integrations e.g. Slack, Salesforce, Zapier"],
    "api_available": true or false,
    "mobile_app_available": true or false,
    "ai_or_ml_features_mentioned": true or false,
    "ai_feature_descriptions": ["specific AI features described"],
    "compliance_mentions": ["GDPR, HIPAA, SOC2, etc"],
    "onboarding_signals": "mention of setup time, migration support, dedicated onboarding or null",
    "support_tiers": ["email | chat | phone | dedicated CSM | 24/7 | SLA-based"]
  }},
  "tech_signals": {{
    "cms_detected": "Shopify | WordPress | Webflow | Contentful | Custom | Unknown",
    "analytics_detected": ["Google Analytics | Segment | Mixpanel | Heap | etc"],
    "ad_pixels_detected": ["Facebook Pixel | LinkedIn Insight | Google Ads | etc"],
    "framework_hints": ["React | Next.js | Vue | etc"],
    "hosting_signals": "AWS | GCP | Azure | Vercel | Cloudflare | unknown"
  }},
  "competitive_moat_signals": {{
    "network_effects_mentioned": true or false,
    "switching_cost_signals": ["data lock-in, migration complexity, deep integrations, long contracts"],
    "proprietary_data_mentioned": true or false,
    "patent_or_ip_mentions": true or false,
    "ecosystem_or_marketplace": true or false
  }},
  "red_flags_and_gaps": ["specific weaknesses, missing features, poor UX signals, negative review mentions, outdated content"],
  "notable_strengths": ["specific, evidence-backed strengths observed"],
  "hiring_signals": ["job titles or departments actively hiring if mentioned — signals growth direction"]
}}

WEBSITE CONTENT:
----------------
{scraped_content}
----------------
Return ONLY the JSON. No commentary. No markdown fences."""


ANALYSIS_PROMPT = """You are producing an executive-grade competitive intelligence analysis. This will be read by C-suite executives making strategic decisions. Be specific, be evidence-backed, be ruthlessly useful.

CONTEXT:
- Our company: {our_company_context}
- Industry: {industry}
- Competitor being analyzed: {company_name}
- Our strategic focus areas: {focus_areas}
- Today's date: {today}

EXTRACTED COMPETITOR DATA:
----------------
{extracted_data}
----------------

Produce the following analysis in valid JSON. Every section must reference specific evidence from the data above.

{{
  "executive_summary": "4-6 sentences. Lead with the single most important strategic implication for us. Cover: who they are, what makes them dangerous or beatable, and the one thing we must do immediately. Be specific.",

  "competitor_snapshot": {{
    "Business Model": "exact model with revenue mechanism",
    "Primary Target Customer": "specific persona, not generic",
    "Price Positioning": "Premium | Mid-Market | Budget | Freemium-to-Paid — with price anchors",
    "Distribution Strategy": "PLG | Sales-led | Channel | Direct | Community — with specifics",
    "Brand Tone": "one word + one sentence justification",
    "Digital Maturity Score": "1-10 with one-line justification",
    "Estimated Market Traction": "any signals: customer count, revenue hints, growth signals",
    "Competitive Moat": "what makes them hard to displace"
  }},

  "strengths": [
    "Format exactly: 'STRENGTH TITLE: [specific observation]. Evidence: [quote or data point]. Implication for us: [what this means].' — 4-6 items."
  ],

  "weaknesses": [
    "Format exactly: 'GAP: [specific weakness observed]. Why it matters: [customer impact]. Our opportunity: [specific move we can make].' — 4-6 items."
  ],

  "opportunities_for_us": [
    "Format exactly: 'OPPORTUNITY: [what we can do]. Based on: [their specific gap]. Expected impact: [qualitative]. → Immediate action: [verb + deliverable in 2 weeks].' — 3-5 items."
  ],

  "threats_to_us": [
    "Format exactly: 'THREAT: [what they could do or are doing]. Severity: High|Med|Low. Timeline: [when this becomes a problem]. Defense: [specific counter-move].' — 3-5 items."
  ],

  "porters_five_forces": {{
    "competitive_rivalry": "assessment based on this competitor's moves",
    "threat_of_new_entrants": "based on observed barriers or lack thereof",
    "bargaining_power_of_buyers": "based on pricing flexibility and switching signals",
    "threat_of_substitutes": "what non-obvious alternatives exist",
    "bargaining_power_of_suppliers": "tech/platform dependencies observed"
  }},

  "swot": {{
    "Strengths": ["their specific strengths — 3-4 items"],
    "Weaknesses": ["their specific gaps — 3-4 items"],
    "Opportunities": ["market opportunities they are pursuing — 2-3 items"],
    "Threats": ["what threatens their position — 2-3 items"]
  }},

  "win_loss_scenarios": {{
    "when_we_win": ["3 specific scenarios where we beat them head-to-head"],
    "when_we_lose": ["3 specific scenarios where they have the advantage"],
    "the_swing_accounts": "describe the type of customer who could go either way and what tips the decision"
  }},

  "next_steps": [
    {{
      "priority": "P0 — This week | P1 — This month | P2 — This quarter",
      "action": "Specific verb + exact deliverable",
      "rationale": "Tied to specific competitor data point",
      "owner": "Marketing | Product | Sales | Founders | Engineering",
      "success_metric": "How we know it worked",
      "estimated_effort": "Hours | Days | Weeks"
    }}
  ],

  "differentiation_strategy": "3-4 sentences. Our positioning angle, the specific wedge to use against this competitor, and one concrete tagline or messaging hook we can test immediately. Be specific about the segment to target first.",

  "pricing_response": "Should we adjust? What specifically? Where are we overpriced or underpriced relative to them? Concrete recommendation.",

  "confidence_assessment": "How complete is this analysis? What is missing that would change the conclusions? What should we manually verify?"
}}

QUALITY RULES:
- Zero generic statements. Every line must be specific.
- Reference competitor data directly (quote it if useful).
- Prioritize ruthlessly — if everything is P0, nothing is.
- The CEO reading this should be able to take action today.
Return ONLY the JSON."""


REPORT_FORMAT_PROMPT = """Convert this competitive analysis JSON into a polished, boardroom-ready Markdown intelligence report. This goes directly to the CEO and strategy team.

Use this exact structure with rich formatting:

# 🎯 Competitive Intelligence Report: {company_name}
**Generated:** {date} | **Confidence Level:** [pull from confidence_assessment] | **Classification:** Confidential

---

## 1. Executive Summary
[executive_summary — formatted as a callout block]

> **Key Strategic Implication:** [extract the single most important action from the summary]

---

## 2. Competitor at a Glance

| Dimension | Assessment |
|-----------|------------|
[fill from competitor_snapshot — one row per dimension]

---

## 3. What They're Doing Well (Strengths)
[strengths — bullet list, bold the strength title, evidence in italics]

---

## 4. Where They're Vulnerable (Weaknesses → Our Opportunities)
[weaknesses — bullet list, bold the gap, our opportunity in a nested bullet]

---

## 5. Strategic Opportunities for Us
[opportunities_for_us — numbered list, bold the opportunity, → Action on its own line]

---

## 6. Threats & Defense Playbook

| Threat | Severity | Timeline | Counter-Move |
|--------|----------|----------|--------------|
[fill from threats_to_us]

---

## 7. Win / Loss Scenarios

### When We Win
[win_loss_scenarios.when_we_win — bullet list]

### When We Lose
[win_loss_scenarios.when_we_lose — bullet list]

### The Swing Account
[win_loss_scenarios.the_swing_accounts]

---

## 8. SWOT Matrix

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **Strengths:** [list] | **Weaknesses:** [list] |
| **External** | **Opportunities:** [list] | **Threats:** [list] |

---

## 9. Porter's Five Forces Assessment
[porters_five_forces — brief paragraph per force]

---

## 10. Recommended Next Steps

| Priority | Action | Owner | Success Metric | Effort |
|----------|--------|-------|----------------|--------|
[fill from next_steps — sorted P0 first]

---

## 11. Pricing Response Recommendation
[pricing_response]

---

## 12. Our Recommended Positioning
[differentiation_strategy — 2-3 paragraphs]

> **Test This Tagline:** [extract the specific tagline from differentiation_strategy]

---

## 13. What to Verify Next
[confidence_assessment]

---
*Generated by Competitive Intelligence AI Engine. Validate all data points before board presentation.*

ANALYSIS JSON:
{analysis_json}"""
