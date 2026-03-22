#!/usr/bin/env python3
"""Morning briefing — run all agent daily tasks and produce unified briefing.

Steps:
    1. Optionally ingest new finance statements.
    2. Run education ingestion.
    3. Generate all agent daily summaries.
    4. Run insight engine to produce unified briefing.
    5. Output JSON + Markdown.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


def run_morning(skip_finance_ingest: bool = False, skip_education_ingest: bool = False) -> None:
    today = date.today()
    log.info("=== Morning Briefing — %s ===", today.strftime("%A %d %B %Y"))

    # 1. Finance ingestion (optional)
    if not skip_finance_ingest:
        log.info("[1/5] Running finance ingestion...")
        try:
            from vaishali.core.config import settings
            from vaishali.core.storage import init_db

            init_db()
            # Only ingest if there are CSV files in the raw dir
            raw = settings.finance_raw_dir
            csvs = list(raw.glob("*.csv"))
            if csvs:
                log.info("Found %d CSV files — ingestion available", len(csvs))
            else:
                log.info("No new finance files to ingest")
        except Exception as e:
            log.warning("Finance ingestion skipped: %s", e)
    else:
        log.info("[1/5] Finance ingestion skipped")

    # 2. Education ingestion
    if not skip_education_ingest:
        log.info("[2/5] Running education ingestion...")
        try:
            from vaishali.education.ingestion import ingest_all

            items = ingest_all(today)
            log.info("Ingested %d education items", len(items))
        except Exception as e:
            log.warning("Education ingestion failed: %s", e)
    else:
        log.info("[2/5] Education ingestion skipped")

    # 3. Generate agent summaries
    log.info("[3/5] Generating agent summaries...")

    try:
        from vaishali.finance.summaries import generate_daily_summary as fin_summary

        fin_summary(today)
    except Exception as e:
        log.warning("Finance summary failed: %s", e)

    try:
        from vaishali.education.summaries import generate_daily_summary as edu_summary

        edu_summary(today)
    except Exception as e:
        log.warning("Education summary failed: %s", e)

    try:
        from vaishali.research.summariser import generate_daily_summary as res_summary

        res_summary(today)
    except Exception as e:
        log.warning("Research summary failed: %s", e)

    try:
        from vaishali.content.summaries import generate_daily_summary as content_summary

        content_summary(today)
    except Exception as e:
        log.warning("Content summary failed: %s", e)

    try:
        from vaishali.health.summaries import generate_daily_summary as health_summary

        health_summary(today)
    except Exception as e:
        log.warning("Health summary failed: %s", e)

    try:
        from vaishali.braindump.summaries import generate_summary as braindump_summary

        braindump_summary(today)
    except Exception as e:
        log.warning("Braindump summary failed: %s", e)

    # 4. Insight engine
    log.info("[4/5] Running insight engine...")
    try:
        from vaishali.insight_engine.engine import generate_briefing

        briefing = generate_briefing(today)
        log.info("[5/5] Briefing complete!")
        log.info("")
        log.info("📌 %s", briefing["what_matters_most_today"])
        log.info("🏆 %s", briefing["todays_win"])
        for insight in briefing.get("cross_agent_insights", []):
            log.info("  • %s", insight)
    except Exception as e:
        log.error("Insight engine failed: %s", e)

    # 6. Sync to Obsidian vault
    log.info("[6/6] Syncing to Obsidian vault...")
    try:
        from vaishali.core.obsidian_sync import sync_all_to_obsidian

        written = sync_all_to_obsidian(today)
        if written:
            log.info("Synced %d notes to Obsidian", written)
        else:
            log.info("Obsidian vault not configured — skipping sync")
    except Exception as e:
        log.warning("Obsidian sync failed: %s", e)

    log.info("=== Morning briefing complete ===")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run morning briefing")
    parser.add_argument("--skip-finance", action="store_true", help="Skip finance ingestion")
    parser.add_argument("--skip-education", action="store_true", help="Skip education ingestion")
    args = parser.parse_args()

    run_morning(
        skip_finance_ingest=args.skip_finance,
        skip_education_ingest=args.skip_education,
    )


if __name__ == "__main__":
    main()
