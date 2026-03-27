#!/usr/bin/env python3
"""
VAF AM Series — Intelligent Delivery Handler
Routes insights to Slack, Telegram, or dashboard based on content type and severity.

Usage:
    from delivery_handler import DeliveryHandler

    handler = DeliveryHandler()
    await handler.deliver(
        content="Portfolio risk alert: XYZ Holdings exposed to new FCA rule",
        content_type="compliance_alert",
        severity="HIGH",
        metadata={"ticker": "XYZ", "impact": "£2M"}
    )
"""

import os
import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
from enum import Enum
from pathlib import Path
import httpx
from dotenv import load_dotenv

load_dotenv()


class ContentType(Enum):
    MORNING_BRIEF = "morning_brief"
    RESEARCH_NOTE = "research_note"
    COMPLIANCE_ALERT = "compliance_alert"
    RISK_ALERT = "risk_alert"
    EARNINGS_SIGNAL = "earnings_signal"
    REGULATORY_UPDATE = "regulatory_update"
    SYSTEM_STATUS = "system_status"


class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class DeliveryPayload:
    """Standardized payload for all delivery channels."""
    id: str
    content: str
    content_type: str
    severity: str
    title: str
    created_at: str
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DeliveryResult:
    """Result of delivery attempt."""
    payload_id: str
    channel: str
    status: str  # "success", "failed", "skipped"
    message_id: Optional[str] = None
    delivered_at: Optional[str] = None
    error: Optional[str] = None


class SlackDelivery:
    """Send messages to Slack."""

    MAX_LENGTH = 4000

    def __init__(self):
        self.webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
        self.enabled = bool(self.webhook_url)

    async def send(self, payload: DeliveryPayload) -> DeliveryResult:
        """Send to Slack webhook."""
        result = DeliveryResult(
            payload_id=payload.id,
            channel="slack",
            status="skipped",
            delivered_at=datetime.utcnow().isoformat(),
        )

        if not self.enabled:
            result.status = "skipped"
            result.error = "SLACK_WEBHOOK_URL not configured"
            return result

        # Format message for Slack
        color_map = {
            "CRITICAL": "#ff0000",
            "HIGH": "#ff6600",
            "MEDIUM": "#ffcc00",
            "LOW": "#00cc00",
        }

        slack_message = {
            "attachments": [{
                "color": color_map.get(payload.severity, "#0066cc"),
                "title": payload.title,
                "text": payload.content[:self.MAX_LENGTH],
                "fields": [
                    {"title": "Type", "value": payload.content_type, "short": True},
                    {"title": "Severity", "value": payload.severity, "short": True},
                ] + [
                    {"title": k, "value": str(v), "short": True}
                    for k, v in (payload.metadata or {}).items()
                ],
                "footer": "VAF AM Series",
                "ts": int(datetime.utcnow().timestamp()),
            }]
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.webhook_url, json=slack_message)
                if resp.status_code == 200:
                    result.status = "success"
                    result.message_id = payload.id
                else:
                    result.status = "failed"
                    result.error = f"HTTP {resp.status_code}"
        except Exception as e:
            result.status = "failed"
            result.error = str(e)

        return result


class TelegramDelivery:
    """Send messages to Telegram."""

    MAX_LENGTH = 4096

    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self.bot_token and self.chat_id)

    async def send(self, payload: DeliveryPayload) -> DeliveryResult:
        """Send to Telegram."""
        result = DeliveryResult(
            payload_id=payload.id,
            channel="telegram",
            status="skipped",
            delivered_at=datetime.utcnow().isoformat(),
        )

        if not self.enabled:
            result.status = "skipped"
            result.error = "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured"
            return result

        # Format message for Telegram
        severity_emoji = {
            "CRITICAL": "🚨",
            "HIGH": "⚠️",
            "MEDIUM": "⚡",
            "LOW": "ℹ️",
        }

        message = f"""
{severity_emoji.get(payload.severity, "📌")} **{payload.title}**

{payload.content[:self.MAX_LENGTH]}

*Type:* {payload.content_type}
*Severity:* {payload.severity}
"""

        if payload.metadata:
            message += "\n*Metadata:*\n"
            for k, v in payload.metadata.items():
                message += f"• {k}: {v}\n"

        message += f"\n_VAF AM Series | {datetime.utcnow().isoformat()}_"

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                })
                data = resp.json()
                if data.get("ok"):
                    result.status = "success"
                    result.message_id = str(data.get("result", {}).get("message_id"))
                else:
                    result.status = "failed"
                    result.error = data.get("description", "Unknown error")
        except Exception as e:
            result.status = "failed"
            result.error = str(e)

        return result


class DashboardDelivery:
    """Log to local JSON for dashboard consumption."""

    def __init__(self, output_dir: Path = Path("outputs")):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.log_file = self.output_dir / "deliveries.json"

    async def send(self, payload: DeliveryPayload) -> DeliveryResult:
        """Log to dashboard JSON."""
        result = DeliveryResult(
            payload_id=payload.id,
            channel="dashboard",
            status="success",
            message_id=payload.id,
            delivered_at=datetime.utcnow().isoformat(),
        )

        try:
            # Load existing deliveries
            deliveries = []
            if self.log_file.exists():
                with open(self.log_file) as f:
                    deliveries = json.load(f)

            # Add new delivery
            deliveries.append({
                **asdict(payload),
                "delivered_at": result.delivered_at,
            })

            # Save
            with open(self.log_file, "w") as f:
                json.dump(deliveries, f, indent=2, default=str)

        except Exception as e:
            result.status = "failed"
            result.error = str(e)

        return result


class DeliveryHandler:
    """Main handler that routes messages to appropriate channels."""

    # Routing rules: content_type -> [channels]
    ROUTING_RULES = {
        ContentType.MORNING_BRIEF.value: ["telegram", "dashboard"],
        ContentType.RESEARCH_NOTE.value: ["slack", "dashboard"],
        ContentType.COMPLIANCE_ALERT.value: ["telegram", "slack", "dashboard"],
        ContentType.RISK_ALERT.value: ["telegram", "slack", "dashboard"],
        ContentType.EARNINGS_SIGNAL.value: ["slack", "dashboard"],
        ContentType.REGULATORY_UPDATE.value: ["telegram", "dashboard"],
        ContentType.SYSTEM_STATUS.value: ["dashboard"],
    }

    # Severity overrides: if CRITICAL, send to all channels
    CRITICAL_OVERRIDE = True

    def __init__(self, output_dir: Path = Path("outputs")):
        self.slack = SlackDelivery()
        self.telegram = TelegramDelivery()
        self.dashboard = DashboardDelivery(output_dir)
        self.output_dir = Path(output_dir)
        self.audit_file = self.output_dir / "delivery_audit.json"
        self.output_dir.mkdir(exist_ok=True)

    async def deliver(
        self,
        content: str,
        content_type: str,
        severity: str = "MEDIUM",
        title: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Deliver a payload to appropriate channels.

        Args:
            content: Message content
            content_type: Type of content (from ContentType enum)
            severity: Severity level (from Severity enum)
            title: Optional title (auto-generated from content if not provided)
            metadata: Optional metadata dict

        Returns:
            dict with delivery results per channel
        """
        import uuid

        # Generate title if not provided
        if not title:
            title = content.split('\n')[0][:100]

        # Create payload
        payload = DeliveryPayload(
            id=str(uuid.uuid4()),
            content=content,
            content_type=content_type,
            severity=severity,
            title=title,
            created_at=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )

        # Determine channels
        channels = self.ROUTING_RULES.get(content_type, ["dashboard"])

        # Override for critical
        if self.CRITICAL_OVERRIDE and severity == "CRITICAL":
            channels = ["slack", "telegram", "dashboard"]

        # Deliver to all channels
        results = {}
        for channel in channels:
            if channel == "slack":
                result = await self.slack.send(payload)
            elif channel == "telegram":
                result = await self.telegram.send(payload)
            else:  # dashboard
                result = await self.dashboard.send(payload)

            results[channel] = asdict(result)

        # Audit log
        await self._audit_delivery(payload, results)

        return results

    async def _audit_delivery(self, payload: DeliveryPayload, results: dict):
        """Log delivery to audit file."""
        try:
            audit_log = []
            if self.audit_file.exists():
                with open(self.audit_file) as f:
                    audit_log = json.load(f)

            audit_log.append({
                "payload_id": payload.id,
                "timestamp": datetime.utcnow().isoformat(),
                "content_type": payload.content_type,
                "severity": payload.severity,
                "results": results,
            })

            with open(self.audit_file, "w") as f:
                json.dump(audit_log, f, indent=2, default=str)
        except Exception as e:
            print(f"[AUDIT ERROR] {e}")


# Example usage
if __name__ == "__main__":

    async def example():
        handler = DeliveryHandler()

        # Example: Regulatory alert
        results = await handler.deliver(
            content="""
FCA Rule Change Alert: New ESG disclosure requirements effective March 2026.

Impact: Affects 340 portfolio holdings across all asset classes.
Action Required: Update fund prospectuses and risk disclosures within 30 days.

Affected Sectors:
- Financials: 45 holdings
- Energy: 28 holdings
- Healthcare: 22 holdings

Next Steps:
1. Review prospectus templates
2. Identify affected funds
3. Coordinate with compliance team
            """,
            content_type="compliance_alert",
            severity="HIGH",
            title="FCA ESG Disclosure Rules — March 2026",
            metadata={
                "ticker": "N/A",
                "impact_holdings": 340,
                "deadline": "2026-04-23",
                "priority": "HIGH"
            }
        )

        print("\n✅ Delivery Results:")
        print(json.dumps(results, indent=2))

    asyncio.run(example())
