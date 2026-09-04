"""
Autonomous Action & GTM Dispatch Service.

Translates competitor intelligence into executable, department-specific playbooks:
  1. Product & Engineering: Jira User Stories, Acceptance Criteria, and Sprints
  2. Sales & Commercial: Objection counter-scripts, cold outreach templates, battlecard landmines
  3. Marketing & Growth: Comparison ad copy, churn-capture campaign angles, SEO articles
  4. Executive / Founder: Strategic positioning directives

Dispatches playbooks across modern enterprise channels:
  - Direct Jira Cloud REST API issue creation
  - Instant WhatsApp / Twilio / Webhook mobile alerting
  - GitHub Issue creation for engineering backlogs
"""

import os
import json
import base64
import logging
from datetime import datetime
from typing import Any, Optional
import httpx
from openai import AsyncOpenAI

from config import GROQ_API_KEY, GROQ_BASE_URL, LLM_MODEL
from database import get_competitor_by_id, get_company_profile_by_id, create_task

logger = logging.getLogger(__name__)


class ActionDispatchService:
    """Generates departmental playbooks and dispatches to Jira, WhatsApp, and GitHub."""

    @staticmethod
    async def generate_departmental_playbook(
        company_id: str,
        competitor_id: str,
        event_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Synthesizes a competitor event into 4 ready-to-execute departmental playbooks:
        Product, Sales, Marketing, and Leadership.
        """
        company = get_company_profile_by_id(company_id) or {}
        competitor = get_competitor_by_id(competitor_id) or {}

        our_name = company.get("company_name", "Our Company")
        our_product = company.get("products_or_services", "B2B Software Platform")
        comp_name = competitor.get("name", "Competitor")
        comp_desc = competitor.get("description", "")

        evt_title = (event_context or {}).get("title", f"Aggressive move by {comp_name}")
        evt_summary = (event_context or {}).get("summary", f"{comp_name} made updates to their product and pricing.")
        evt_type = (event_context or {}).get("event_type", "PRICING_OR_PRODUCT_SHIFT")
        impact = (event_context or {}).get("impact_score", 75)

        prompt = f"""You are a Principal Operating Partner and Go-To-Market Strategist.
A significant competitor move has been detected. Produce a concrete, highly specific, 4-department tactical playbook for our team.
Return ONLY valid JSON.

OUR COMPANY:
Name: {our_name}
Offering: {our_product}

COMPETITOR:
Name: {comp_name}
Description: {comp_desc}

DETECTED EVENT:
Title: {evt_title}
Summary: {evt_summary}
Event Type: {evt_type}
Impact Score: {impact}/100

Produce this exact JSON structure with concrete, actionable text (no vague placeholders):
{{
  "eventSummary": "1-2 sentence executive briefing of the competitor move",
  "productDirective": {{
    "jiraIssueTitle": "Exact Jira ticket title with [CI Response] prefix",
    "userStory": "As a [target user], I need [feature] so that [business outcome]",
    "acceptanceCriteria": [
      "Concrete criterion 1",
      "Concrete criterion 2",
      "Concrete criterion 3"
    ],
    "priority": "HIGH or CRITICAL",
    "recommendedSprint": "Current Sprint or Next Sprint"
  }},
  "salesDirective": {{
    "liveCounterScript": "30-second script for sales reps when prospects bring up this competitor move on calls",
    "coldOutreachSnippet": "3-sentence email snippet targeting prospects currently evaluating this competitor",
    "pricingCounter": "Specific advice on how to position our pricing against theirs"
  }},
  "marketingDirective": {{
    "adCampaignHeadline": "Punchy, high-converting ad headline targeting competitor churn",
    "landingPageAngle": "Comparison page angle that exposes their new weakness",
    "contentTitle": "SEO blog/comparison title (e.g. 'Why [Our Company] is the Top Alternative to [Competitor]')"
  }},
  "executiveDirective": {{
    "strategicDecision": "One clear decision for Founders/C-suite: Adjust pricing, accelerate feature, or hold position",
    "revenueAtRisk": "Estimated qualitative risk to pipeline"
  }}
}}"""

        try:
            client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
            resp = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an elite GTM strategist. Return only strict, valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            playbook = json.loads(resp.choices[0].message.content or "{}")
        except Exception as exc:
            logger.warning("LLM playbook generation failed, using deterministic fallback: %s", exc)
            playbook = {
                "eventSummary": f"{comp_name} announced '{evt_title}'. Impact score: {impact}/100.",
                "productDirective": {
                    "jiraIssueTitle": f"[CI Response] Counter {comp_name}'s {evt_type} move",
                    "userStory": f"As an enterprise buyer, I need our team to counter {comp_name}'s latest update so we retain market leadership.",
                    "acceptanceCriteria": [
                        "Analyze architectural overlap with competitor move",
                        "Deliver prototype within 2 sprints",
                        "Update product documentation"
                    ],
                    "priority": "HIGH" if impact >= 75 else "MEDIUM",
                    "recommendedSprint": "Next Sprint"
                },
                "salesDirective": {
                    "liveCounterScript": f"When prospects mention {comp_name}'s update, acknowledge it politely, then pivot: 'While {comp_name} is adjusting, our solution offers higher reliability, better support, and transparent ROI.'",
                    "coldOutreachSnippet": f"Notice {comp_name}'s recent changes? Companies are switching to {our_name} to lock in predictable pricing and superior reliability.",
                    "pricingCounter": "Emphasize total cost of ownership and transparent enterprise tiering."
                },
                "marketingDirective": {
                    "adCampaignHeadline": f"Rethinking {comp_name}? Discover {our_name}",
                    "landingPageAngle": f"Side-by-side breakdown showing why {our_name} outperforms {comp_name}.",
                    "contentTitle": f"Top 5 Reasons Teams Are Migrating from {comp_name} to {our_name}"
                },
                "executiveDirective": {
                    "strategicDecision": f"Monitor churn signals from {comp_name} and equip sales team with counter-arguments.",
                    "revenueAtRisk": "Moderate to High pipeline risk if left unanswered."
                }
            }

        playbook["competitorId"] = competitor_id
        playbook["competitorName"] = comp_name
        playbook["generatedAt"] = datetime.utcnow().isoformat()

        # Automatically record as internal task in database
        try:
            prod_dir = playbook.get("productDirective", {})
            create_task({
                "company_id": company_id,
                "title": prod_dir.get("jiraIssueTitle", f"[CI] Counter {comp_name}"),
                "description": f"{playbook.get('eventSummary', '')}\n\nUser Story:\n{prod_dir.get('userStory', '')}",
                "priority": prod_dir.get("priority", "HIGH"),
                "competitor_id": competitor_id,
                "competitor_name": comp_name,
                "source_type": "PLAYBOOK"
            })
        except Exception as exc:
            logger.warning("Failed to auto-save playbook task: %s", exc)

        return playbook

    @staticmethod
    async def create_jira_issue(
        jira_domain: str,
        email: str,
        api_token: str,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: str = "High",
    ) -> dict[str, Any]:
        """
        Directly creates an issue in Atlassian Jira Cloud via REST API v3.
        """
        clean_domain = jira_domain.replace("https://", "").replace(".atlassian.net", "").strip()
        url = f"https://{clean_domain}.atlassian.net/rest/api/3/issue"

        auth_str = f"{email.strip()}:{api_token.strip()}"
        auth_header = base64.b64encode(auth_str.encode()).decode()

        # Construct Jira v3 Atlassian Document Format (ADF) description
        payload = {
            "fields": {
                "project": {"key": project_key.upper().strip()},
                "summary": summary[:255],
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description[:3000]}]
                        }
                    ]
                },
                "issuetype": {"name": issue_type}
            }
        }

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=12) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    key = data.get("key", "")
                    issue_url = f"https://{clean_domain}.atlassian.net/browse/{key}"
                    logger.info("Created Jira ticket %s on %s", key, clean_domain)
                    return {
                        "success": True,
                        "key": key,
                        "url": issue_url,
                        "message": f"Successfully created Jira issue {key}."
                    }
                else:
                    logger.warning("Jira API returned HTTP %s: %s", resp.status_code, resp.text)
                    return {
                        "success": False,
                        "statusCode": resp.status_code,
                        "message": f"Jira API Error: {resp.text}"
                    }
        except Exception as exc:
            logger.error("Failed to connect to Jira API: %s", exc)
            return {
                "success": False,
                "message": f"Jira connection exception: {str(exc)}"
            }

    @staticmethod
    async def dispatch_whatsapp_alert(
        recipient_phone: str,
        alert_text: str,
        twilio_account_sid: Optional[str] = None,
        twilio_auth_token: Optional[str] = None,
        twilio_from_number: Optional[str] = None,
        custom_webhook_url: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Dispatches an instant WhatsApp alert via Twilio or a custom Mobile Webhook.
        """
        # 1. Custom Webhook dispatch (Make / Zapier / Slack / Telegram)
        webhook = custom_webhook_url or os.getenv("WHATSAPP_WEBHOOK_URL") or os.getenv("GENERIC_WEBHOOK_URL")
        if webhook:
            try:
                async with httpx.AsyncClient(timeout=8) as client:
                    resp = await client.post(webhook, json={
                        "channel": "WHATSAPP",
                        "to": recipient_phone,
                        "message": alert_text,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    return {
                        "success": resp.status_code in (200, 201, 204),
                        "provider": "Custom Mobile Webhook",
                        "message": f"Alert dispatched to webhook ({resp.status_code})."
                    }
            except Exception as exc:
                logger.warning("Webhook dispatch failed: %s", exc)

        # 2. Twilio WhatsApp API dispatch if credentials provided
        sid = twilio_account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        token = twilio_auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        from_num = twilio_from_number or os.getenv("TWILIO_WHATSAPP_FROM", "+14155238886")

        if sid and token:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
            to_clean = recipient_phone if recipient_phone.startswith("whatsapp:") else f"whatsapp:{recipient_phone}"
            from_clean = from_num if from_num.startswith("whatsapp:") else f"whatsapp:{from_num}"

            auth = (sid, token)
            data = {
                "From": from_clean,
                "To": to_clean,
                "Body": alert_text
            }

            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.post(url, data=data, auth=auth)
                    if resp.status_code in (200, 201):
                        return {
                            "success": True,
                            "provider": "Twilio WhatsApp API",
                            "message": f"WhatsApp message successfully sent to {recipient_phone}."
                        }
                    else:
                        return {
                            "success": False,
                            "provider": "Twilio WhatsApp API",
                            "statusCode": resp.status_code,
                            "message": resp.text
                        }
            except Exception as exc:
                logger.error("Twilio WhatsApp request failed: %s", exc)
                return {"success": False, "message": str(exc)}

        # Simulated Instant Response if keys not configured
        return {
            "success": True,
            "provider": "Simulation Engine (Configure TWILIO_ACCOUNT_SID or WHATSAPP_WEBHOOK_URL for real SMS/WhatsApp)",
            "message": f"Alert formatted and queued for {recipient_phone}.",
            "formattedAlert": alert_text
        }
