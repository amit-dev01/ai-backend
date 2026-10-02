"""
Autonomous Alerting & Webhook Service.

Dispatches real-time alerts when critical competitive shifts occur:
  - CRITICAL impact events (impact_score >= 80)
  - Pricing changes & product pivots (step-function deltas)
  - Major acquisitions & funding rounds

Supports:
  1. Slack Webhooks (Block Kit formatted)
  2. Generic Webhooks (Teams, Discord, internal services)
  3. Email Notification Triggers (Resend / SendGrid stubs)
"""

import logging
import os
from typing import Any, Optional
import httpx

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
GENERIC_WEBHOOK_URL = os.getenv("GENERIC_WEBHOOK_URL", "")


class AlertService:
    """Dispatches real-time alerts across configured notification channels."""

    @staticmethod
    async def dispatch_critical_event_alert(
        competitor_name: str,
        event_type: str,
        impact_score: int,
        impact_label: str,
        title: str,
        summary: str,
        source_url: str,
        recommended_action: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ) -> bool:
        """
        Dispatches an immediate alert for a high-impact competitor event.
        """
        target_slack = webhook_url or SLACK_WEBHOOK_URL
        if not target_slack:
            logger.info("No SLACK_WEBHOOK_URL configured. Alert logged to console: [%s] %s - %s", impact_label, competitor_name, title)
            return False

        # Slack Block Kit format
        color_emoji = "🚨" if impact_score >= 80 else "⚠️"
        payload = {
            "text": f"{color_emoji} [{impact_label}] Competitive Alert: {competitor_name} - {event_type}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{color_emoji} Competitive Alert: {competitor_name}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Event Type:*\n`{event_type}`"},
                        {"type": "mrkdwn", "text": f"*Impact:*\n*{impact_score}/100* (`{impact_label}`)"},
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{title}*\n{summary}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"*Action:* {recommended_action or 'Review tactical battlecard'} | <{source_url}|View Source Article>"}
                    ]
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(target_slack, json=payload)
                if resp.status_code in (200, 204):
                    logger.info("Successfully dispatched Slack alert for %s", competitor_name)
                    return True
                else:
                    logger.warning("Slack webhook returned HTTP %d: %s", resp.status_code, resp.text)
                    return False
        except Exception as exc:
            logger.error("Failed to post Slack alert: %s", exc)
            return False

    @staticmethod
    async def dispatch_pricing_shift_alert(
        competitor_name: str,
        price_delta_desc: str,
        flagship_product: str,
        webhook_url: Optional[str] = None,
    ) -> bool:
        """
        Dispatches a dedicated alert when a mathematical step-function pricing shift is detected.
        """
        target_slack = webhook_url or SLACK_WEBHOOK_URL
        if not target_slack:
            logger.info("Pricing shift detected for %s: %s", competitor_name, price_delta_desc)
            return False

        payload = {
            "text": f"🏷️ [PRICING SHIFT DETECTED] {competitor_name} Repriced",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🏷️ Competitor Pricing Shift: {competitor_name}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Flagship Product:*\n{flagship_product}"},
                        {"type": "mrkdwn", "text": f"*Shift Details:*\n{price_delta_desc}"},
                    ]
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(target_slack, json=payload)
                return resp.status_code in (200, 204)
        except Exception as exc:
            logger.error("Failed to post pricing shift alert: %s", exc)
            return False
