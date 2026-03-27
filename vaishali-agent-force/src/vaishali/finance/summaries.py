"""Generate machine-readable JSON summaries for the finance agent."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from vaishali.core.logging_utils import get_logger
from vaishali.core.summaries import write_summary
from vaishali.finance import analytics

log = get_logger(__name__)


def generate_daily_summary(day: date | None = None) -> Path:
    """Write data/summaries/finance/YYYY-MM-DD.json with today's finance snapshot."""
    day = day or date.today()

    balances = analytics.balances_by_account()
    net_7d = analytics.net_change(days=7)
    net_30d = analytics.net_change(days=30)
    anomalies = analytics.detect_anomalies()
    recurring = analytics.detect_recurring()

    total_balance = sum(b.balance for b in balances)

    data = {
        "date": day.isoformat(),
        "agent": "finance",
        "total_balance_gbp": float(total_balance),
        "accounts": [
            {
                "id": b.account_id,
                "balance": float(b.balance),
                "tx_count": b.tx_count,
                "net_7d": float(net_7d.get(b.account_id, 0)),
                "net_30d": float(net_30d.get(b.account_id, 0)),
            }
            for b in balances
        ],
        "anomalies": [
            {
                "date": a.tx_date.isoformat(),
                "description": a.description,
                "amount": float(a.amount),
                "reason": a.reason,
                "severity": a.severity,
            }
            for a in anomalies[:10]
        ],
        "recurring_count": len(recurring),
        "headline": _build_headline(total_balance, net_7d, anomalies),
        "status": _derive_status(anomalies),
        "mood": _derive_mood(anomalies, total_balance),
    }

    return write_summary("finance", data, day)


def _derive_status(anomalies) -> str:
    """Derive agent visual status: idle | success | warning | running."""
    if any(a.severity == "high" for a in anomalies):
        return "warning"
    if anomalies:
        return "success"  # has data, minor anomalies
    return "success"


def _derive_mood(anomalies, total_balance) -> str:
    """One-line mood phrase for the Agent Strip."""
    if any(a.severity == "high" for a in anomalies):
        return f"Watching {len(anomalies)} anomal{'ies' if len(anomalies) > 1 else 'y'}"
    return "All accounts healthy"


def _build_headline(total_balance, net_7d, anomalies) -> str:
    """One-line human-readable finance status."""
    total_net_7d = sum(net_7d.values())
    direction = "up" if total_net_7d >= 0 else "down"
    anomaly_note = f" — {len(anomalies)} anomalies flagged" if anomalies else ""
    return (
        f"Total balance £{total_balance:,.2f}, "
        f"{direction} £{abs(total_net_7d):,.2f} over 7 days"
        f"{anomaly_note}"
    )
