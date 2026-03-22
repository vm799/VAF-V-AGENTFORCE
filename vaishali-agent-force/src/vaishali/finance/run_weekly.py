#!/usr/bin/env python3
"""Weekly finance orchestration: analyse → weekly report → daily summary."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "src"))

from vaishali.core.logging_utils import get_logger
from vaishali.finance.reports import generate_weekly_report
from vaishali.finance.summaries import generate_daily_summary

log = get_logger(__name__)


def run(end_date: date | None = None) -> None:
    """Execute the weekly finance pipeline."""
    end_date = end_date or date.today()
    log.info("═══ Finance Weekly Pipeline — ending %s ═══", end_date.isoformat())

    log.info("Step 1/2: Generating weekly report…")
    report = generate_weekly_report(end_date)
    log.info("  → %s", report)

    log.info("Step 2/2: Generating daily summary…")
    summary = generate_daily_summary(end_date)
    log.info("  → %s", summary)

    log.info("═══ Finance weekly pipeline complete ═══")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--end-date", type=date.fromisoformat, default=None)
    args = parser.parse_args()
    run(end_date=args.end_date)
