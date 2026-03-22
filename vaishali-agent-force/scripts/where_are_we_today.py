#!/usr/bin/env python3
"""Quick finance status check — "Where are we today?"

Prints a short human-readable finance summary to stdout.
Optionally writes reports/finance/today.md.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger
from vaishali.core.storage import init_db
from vaishali.finance import analytics

log = get_logger(__name__)


def where_are_we_today(write_file: bool = False) -> str:
    """Build and return a short finance snapshot."""
    init_db()

    balances = analytics.balances_by_account()
    net_7d = analytics.net_change(days=7)
    net_30d = analytics.net_change(days=30)
    anomalies = analytics.detect_anomalies()

    today = date.today()
    total = sum(b.balance for b in balances)
    total_7d = sum(net_7d.values())
    total_30d = sum(net_30d.values())

    lines = [
        f"💰 Where Are We Today? — {today.strftime('%A %d %B %Y')}",
        f"{'─' * 50}",
    ]

    if not balances:
        lines.append("No financial data yet. Run ingestion first.")
    else:
        lines.append(f"Total balance: £{total:,.2f}")
        lines.append(f"  7-day change:  £{total_7d:+,.2f}")
        lines.append(f"  30-day change: £{total_30d:+,.2f}")
        lines.append("")

        for b in balances:
            n7 = net_7d.get(b.account_id, 0)
            lines.append(f"  {b.account_id}: £{b.balance:,.2f} (7d: £{n7:+,.2f}, {b.tx_count} txns)")

        if anomalies:
            lines.append(f"\n⚠ {len(anomalies)} anomalies flagged:")
            for a in anomalies[:5]:
                lines.append(f"  • {a.description[:45]} — £{abs(a.amount):,.2f} ({a.reason})")

    output = "\n".join(lines)

    if write_file:
        path = settings.reports_dir / "finance" / "today.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8")
        log.info("Written → %s", path)

    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Quick finance status check")
    parser.add_argument("--write", action="store_true", help="Also write to reports/finance/today.md")
    args = parser.parse_args()

    print(where_are_we_today(write_file=args.write))


if __name__ == "__main__":
    main()
