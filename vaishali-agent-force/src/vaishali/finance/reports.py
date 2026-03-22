"""Generate Markdown finance reports — daily and weekly."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger
from vaishali.finance import analytics

log = get_logger(__name__)


def generate_daily_report(day: date | None = None) -> Path:
    """Create a Markdown daily finance report."""
    day = day or date.today()
    balances = analytics.balances_by_account()
    net_7d = analytics.net_change(days=7)
    net_30d = analytics.net_change(days=30)
    anomalies = analytics.detect_anomalies()
    recurring = analytics.detect_recurring()
    daily = analytics.daily_totals(days=7)

    lines = [
        f"# Finance Daily Report — {day.strftime('%A %d %B %Y')}",
        "",
        "## Account Balances",
        "",
    ]

    if balances:
        lines.append("| Account | Balance | Transactions |")
        lines.append("|---------|--------:|-------------:|")
        for b in balances:
            lines.append(f"| {b.account_id} | £{b.balance:,.2f} | {b.tx_count} |")
    else:
        lines.append("_No accounts with data._")

    lines += ["", "## Net Change", ""]
    lines.append("| Account | 7-day | 30-day |")
    lines.append("|---------|------:|-------:|")
    all_accounts = {b.account_id for b in balances}
    for acct in sorted(all_accounts):
        n7 = net_7d.get(acct, 0)
        n30 = net_30d.get(acct, 0)
        lines.append(f"| {acct} | £{n7:,.2f} | £{n30:,.2f} |")

    if anomalies:
        lines += ["", "## Anomalies", ""]
        for a in anomalies[:10]:
            badge = {"low": "🟡", "medium": "🟠", "high": "🔴"}.get(a.severity, "⚪")
            lines.append(f"- {badge} **{a.description[:50]}** — £{abs(a.amount):,.2f} ({a.reason})")

    if recurring:
        lines += ["", "## Recurring Payments", ""]
        for r in recurring[:10]:
            lines.append(
                f"- **{r['description'][:50]}** — {r['count']}× avg £{abs(r['avg_amount']):,.2f} (last: {r['last_date']})"
            )

    if daily:
        lines += ["", "## Last 7 Days", ""]
        lines.append("| Date | Net | Txns |")
        lines.append("|------|----:|-----:|")
        for d in daily[-7:]:
            lines.append(f"| {d['date']} | £{d['net']:,.2f} | {d['count']} |")

    lines += ["", f"---\n_Generated {day.isoformat()}_"]

    report_path = settings.reports_dir / "finance" / "daily" / f"{day.isoformat()}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Daily finance report → %s", report_path.name)
    return report_path


def generate_weekly_report(end_date: date | None = None) -> Path:
    """Create a Markdown weekly finance report (Mon–Sun ending on *end_date*)."""
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=6)
    week_label = end_date.strftime("%Y-W%W")

    balances = analytics.balances_by_account()
    net_7d = analytics.net_change(days=7)
    categories = analytics.monthly_by_category(end_date.year, end_date.month)
    recurring = analytics.detect_recurring()

    lines = [
        f"# Finance Weekly Report — {start_date.strftime('%d %b')} to {end_date.strftime('%d %b %Y')}",
        "",
        "## Balances",
        "",
    ]

    if balances:
        lines.append("| Account | Balance | 7-day Net |")
        lines.append("|---------|--------:|----------:|")
        for b in balances:
            n7 = net_7d.get(b.account_id, 0)
            lines.append(f"| {b.account_id} | £{b.balance:,.2f} | £{n7:,.2f} |")

    if categories:
        lines += ["", "## Spending by Category (this month)", ""]
        lines.append("| Category | Total | Txns |")
        lines.append("|----------|------:|-----:|")
        for c in categories:
            lines.append(f"| {c.category} | £{c.total:,.2f} | {c.count} |")

    if recurring:
        lines += ["", "## Recurring Payments", ""]
        for r in recurring[:10]:
            lines.append(f"- {r['description'][:50]} — {r['count']}× avg £{abs(r['avg_amount']):,.2f}")

    lines += ["", f"---\n_Generated {end_date.isoformat()}_"]

    report_path = settings.reports_dir / "finance" / "weekly" / f"{week_label}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Weekly finance report → %s", report_path.name)
    return report_path
