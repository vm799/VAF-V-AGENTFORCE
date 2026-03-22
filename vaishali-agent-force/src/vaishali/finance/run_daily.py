#!/usr/bin/env python3
"""Daily finance orchestration: ingest → analyse → report → summary."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "src"))

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger
from vaishali.finance.reports import generate_daily_report
from vaishali.finance.summaries import generate_daily_summary

log = get_logger(__name__)


def run(day: date | None = None, ingest: bool = False) -> None:
    """Execute the daily finance pipeline."""
    day = day or date.today()
    log.info("═══ Finance Daily Pipeline — %s ═══", day.isoformat())

    # Step 1: Optional ingestion
    if ingest:
        from scripts.ingest_finance_statements import ingest as do_ingest

        log.info("Step 1/3: Ingesting new statements…")
        do_ingest(
            input_dir=settings.icloud_statements_dir,
            archive_dir=settings.finance_archive_dir,
        )
    else:
        log.info("Step 1/3: Ingestion skipped (use --ingest to enable)")

    # Step 2: Generate report
    log.info("Step 2/3: Generating daily report…")
    report = generate_daily_report(day)
    log.info("  → %s", report)

    # Step 3: Generate JSON summary
    log.info("Step 3/3: Generating daily summary…")
    summary = generate_daily_summary(day)
    log.info("  → %s", summary)

    log.info("═══ Finance daily pipeline complete ═══")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--ingest", action="store_true", help="Run ingestion before analytics")
    parser.add_argument("--date", type=date.fromisoformat, default=None)
    args = parser.parse_args()
    run(day=args.date, ingest=args.ingest)
