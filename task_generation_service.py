import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from database import check_task_exists_for_source, create_task, supabase_client, get_company_profile_by_id, get_competitor_by_id
from discovery_service import _call_groq_json

logger = logging.getLogger(__name__)

class TaskGenerationService:
    
    @staticmethod
    async def generateTaskFromDocument(document_id: str, company_id: str) -> Optional[Dict[str, Any]]:
        if check_task_exists_for_source("source_document_id", document_id):
            return None
            
        try:
            res = supabase_client.table("documents").select("*").eq("id", document_id).limit(1).execute()
            if not res.data: return None
            document = res.data[0]
            
            company = get_company_profile_by_id(company_id)
            if not company: return None
            
            comp_id = document.get("competitor_id")
            comp = get_competitor_by_id(comp_id) if comp_id else None
            
            products = company.get('products_or_services', [])
            products_str = ", ".join(products) if isinstance(products, list) else str(products)
            
            prompt = f"""You are a competitive intelligence analyst and strategic advisor.
A significant competitive event has been detected. Generate a specific
actionable task for the company to respond to this event.
Return only valid JSON, no explanation, no markdown.

OUR COMPANY:
Name: {company.get('company_name', 'Unknown')}
Industry: {company.get('industry', 'Unknown')}
Description: {company.get('description', '')}
Products: {products_str}
Problem Solved: {company.get('primary_problem_solved', '')}

COMPETITIVE EVENT:
Competitor: {comp.get('name') if comp else document.get('competitor_name')}
Event Type: {document.get('event_type')}
Summary: {document.get('summary')}
Impact Level: {document.get('impact_label')}
Impact Score: {document.get('impact_score')}
Sentiment: {document.get('sentiment')}

Return this JSON:
{{
  "title": "string, action-oriented task title max 80 characters, must start with a verb like Analyze, Review, Update, Respond, Investigate, Monitor, Prepare, Create",
  "description": "string, 2 to 3 sentences explaining the competitive context and why this task matters now",
  "recommendedSteps": "string, 3 to 5 specific bullet point action steps the team should take, each on a new line starting with a dash character",
  "priority": "one of CRITICAL or HIGH or MEDIUM or LOW, must match the impact level: CRITICAL impact = CRITICAL priority, HIGH impact = HIGH priority",
  "category": "one of RESPOND_TO_COMPETITOR or MONITOR_SITUATION or UPDATE_STRATEGY or RESEARCH_FURTHER or INTERNAL_ACTION or PRICING_RESPONSE or PRODUCT_RESPONSE, choose based on event type: PRICING_CHANGE = PRICING_RESPONSE, PRODUCT_LAUNCH = PRODUCT_RESPONSE, FUNDING or ACQUISITION = RESPOND_TO_COMPETITOR, HIRING = MONITOR_SITUATION, EXPANSION = UPDATE_STRATEGY",
  "suggestedDueDays": "integer, number of days from now until due, CRITICAL = 3, HIGH = 7, MEDIUM = 14, LOW = 30"
}}"""

            task_json = await _call_groq_json(prompt)
            if not task_json: return None
            
            due_days = task_json.get("suggestedDueDays", 7)
            due_date = (datetime.utcnow() + timedelta(days=due_days)).isoformat()
            
            payload = {
                "company_id": company_id,
                "title": str(task_json.get("title", ""))[:80],
                "description": task_json.get("description"),
                "recommended_steps": task_json.get("recommendedSteps"),
                "priority": task_json.get("priority", "HIGH"),
                "status": "TODO",
                "category": task_json.get("category", "RESPOND_TO_COMPETITOR"),
                "source_type": "AI_GENERATED",
                "source_document_id": document_id,
                "competitor_id": comp_id,
                "competitor_name": comp.get("name") if comp else document.get("competitor_name"),
                "event_type": document.get("event_type"),
                "impact_score": document.get("impact_score"),
                "due_date": due_date
            }
            return create_task(payload)
        except Exception as e:
            logger.exception("Failed to generate task from document: %s", str(e))
            return None

    @staticmethod
    async def generateTaskFromTrend(trend_id: str, company_id: str) -> Optional[Dict[str, Any]]:
        if check_task_exists_for_source("source_trend_id", trend_id):
            return None
        
        try:
            # Placeholder for trend fetch since table schema isn't fully defined in my context
            res = supabase_client.table("competitor_trends").select("*").eq("id", trend_id).limit(1).execute()
            if not res.data: return None
            trend = res.data[0]

            company = get_company_profile_by_id(company_id)
            if not company: return None

            prompt = f"""You are a competitive intelligence analyst. A competitive trend has
been detected that requires strategic attention.
Return only valid JSON, no explanation, no markdown.

OUR COMPANY:
Name: {company.get('company_name', 'Unknown')}
Industry: {company.get('industry', 'Unknown')}
Description: {company.get('description', '')}

TREND DETECTED:
Competitor: {trend.get('competitor_name')}
Trend Type: {trend.get('trend_type')}
Description: {trend.get('description')}
Severity: {trend.get('severity')}
Change: {trend.get('change_percent', 0)}% above or below baseline
Strategic Implication: {trend.get('strategic_implication')}

Return this JSON:
{{
  "title": "string, action-oriented task title max 80 characters",
  "description": "string, 2 to 3 sentences of context",
  "recommendedSteps": "string, 3 specific action steps each on new line starting with dash",
  "priority": "one of CRITICAL or HIGH or MEDIUM",
  "category": "one of MONITOR_SITUATION or UPDATE_STRATEGY or RESPOND_TO_COMPETITOR or RESEARCH_FURTHER",
  "suggestedDueDays": "integer"
}}"""

            task_json = await _call_groq_json(prompt)
            if not task_json: return None
            
            due_days = task_json.get("suggestedDueDays", 7)
            due_date = (datetime.utcnow() + timedelta(days=due_days)).isoformat()

            payload = {
                "company_id": company_id,
                "title": str(task_json.get("title", ""))[:80],
                "description": task_json.get("description"),
                "recommended_steps": task_json.get("recommendedSteps"),
                "priority": task_json.get("priority", "HIGH"),
                "status": "TODO",
                "category": task_json.get("category", "MONITOR_SITUATION"),
                "source_type": "AI_GENERATED",
                "source_trend_id": trend_id,
                "competitor_id": trend.get("competitor_id"),
                "competitor_name": trend.get("competitor_name"),
                "due_date": due_date
            }
            return create_task(payload)
        except Exception as e:
            logger.exception("Failed to generate task from trend: %s", str(e))
            return None

    @staticmethod
    async def generateTaskFromAnomaly(anomaly_id: str, company_id: str) -> Optional[Dict[str, Any]]:
        if check_task_exists_for_source("source_anomaly_id", anomaly_id):
            return None
        
        try:
            # Placeholder for anomaly fetch
            res = supabase_client.table("anomalies").select("*").eq("id", anomaly_id).limit(1).execute()
            if not res.data: return None
            anomaly = res.data[0]

            company = get_company_profile_by_id(company_id)
            if not company: return None

            prompt = f"""You are a competitive intelligence analyst. An unusual pattern has
been detected in competitor behavior that warrants investigation.
Return only valid JSON, no explanation, no markdown.

OUR COMPANY:
Name: {company.get('company_name', 'Unknown')}
Industry: {company.get('industry', 'Unknown')}

ANOMALY DETECTED:
Competitor: {anomaly.get('competitor_name')}
Anomaly Type: {anomaly.get('anomaly_type')}
Description: {anomaly.get('description')}
Severity: {anomaly.get('severity')}
Observed: {anomaly.get('observed_value')} vs Expected: {anomaly.get('expected_value')}
Strategic Implication: {anomaly.get('strategic_implication')}

Return this JSON:
{{
  "title": "string, action-oriented task title max 80 characters",
  "description": "string, 2 to 3 sentences",
  "recommendedSteps": "string, 2 to 3 action steps",
  "priority": "one of CRITICAL or HIGH or MEDIUM",
  "category": "one of RESEARCH_FURTHER or MONITOR_SITUATION",
  "suggestedDueDays": "integer"
}}"""
            task_json = await _call_groq_json(prompt)
            if not task_json: return None
            
            due_days = task_json.get("suggestedDueDays", 7)
            due_date = (datetime.utcnow() + timedelta(days=due_days)).isoformat()

            payload = {
                "company_id": company_id,
                "title": str(task_json.get("title", ""))[:80],
                "description": task_json.get("description"),
                "recommended_steps": task_json.get("recommendedSteps"),
                "priority": task_json.get("priority", "HIGH"),
                "status": "TODO",
                "category": task_json.get("category", "RESEARCH_FURTHER"),
                "source_type": "AI_GENERATED",
                "source_anomaly_id": anomaly_id,
                "competitor_id": anomaly.get("competitor_id"),
                "competitor_name": anomaly.get("competitor_name"),
                "due_date": due_date
            }
            return create_task(payload)
        except Exception as e:
            logger.exception("Failed to generate task from anomaly: %s", str(e))
            return None
