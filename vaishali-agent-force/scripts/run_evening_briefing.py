#!/usr/bin/env python3
"""Evening briefing — summarise the day and update briefing.

Steps:
    1. Re-generate finance summary with latest data.
    2. Re-generate health summary (capture late check-ins).
    3. Update content summary.
    4. Re-run insight engine with updated data.
    5. Output evening-specific observations.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


def run_evening() -> None:
    today = date.today()
    log.info("=== Evening Briefing — %s ===", today.strftime("%A %d %B %Y"))

    # 1. Re-generate finance summary
    log.info("[1/4] Updating finance summary...")
    try:
        from vaishali.core.storage import init_db
        from vaishali.finance.summaries import generate_daily_summary as fin_summary

        init_db()
        fin_summary(today)
    except Exception as e:
        log.warning("Finance summary update failed: %s", e)

    # 2. Re-generate health summary (evening check-in)
    log.info("[2/4] Updating health summary...")
    try:
        from vaishali.health.summaries import generate_daily_summary as health_summary

        health_summary(today)
    except Exception as e:
        log.warning("Health summary update failed: %s", e)

    # 3. Update content summary
    log.info("[3/4] Updating content summary...")
    try:
        from vaishali.content.summaries import generate_daily_summary as content_summary

        content_summary(today)
    except Exception as e:
        log.warning("Content summary update failed: %s", e)

    # 4. Run insight engine with updated data
    log.info("[4/4] Running insight engine...")
    try:
        from vaishali.insight_engine.engine import generate_briefing

        briefing = generate_briefing(today)
        log.info("")
        log.info("📌 %s", briefing["what_matters_most_today"])
        log.info("🏆 %s", briefing["todays_win"])
        for insight in briefing.get("cross_agent_insights", []):
            log.info("  • %s", insight)
    except Exception as e:
        log.error("Insight engine failed: %s", e)

    log.info("=== Evening briefing complete ===")


if __name__ == "__main__":
    run_evening()
