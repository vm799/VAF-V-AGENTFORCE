"""Generate daily content summary JSON."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from vaishali.content.backlog import get_drafts_waiting_review, get_ideas, load_backlog
from vaishali.content.scoring import top_ideas
from vaishali.core.logging_utils import get_logger
from vaishali.core.summaries import write_summary

log = get_logger(__name__)


def generate_daily_summary(day: date | None = None) -> Path:
    """Write data/summaries/content/YYYY-MM-DD.json."""
    day = day or date.today()

    all_items = load_backlog()
    ideas = get_ideas()
    top = top_ideas(ideas, n=5)
    waiting = get_drafts_waiting_review()

    data: dict[str, Any] = {
        "date": day.isoformat(),
        "agent": "content",
        "total_backlog": len(all_items),
        "ideas_count": len(ideas),
        "top_ideas": [
            {
                "id": i.id,
                "title": i.title,
                "type": i.type,
                "channel": i.target_channel,
                "effort": i.effort_estimate,
                "impact": i.impact_estimate,
            }
            for i in top
        ],
        "drafts_waiting_review": [
            {"id": d.id, "title": d.title, "type": d.type}
            for d in waiting
        ],
        "headline": _build_headline(all_items, top, waiting),
        "status": "warning" if waiting else ("success" if top else "idle"),
        "mood": (
            f"{len(waiting)} draft{'s' if len(waiting) > 1 else ''} ready for review"
            if waiting
            else (f"{len(top)} fresh idea{'s' if len(top) > 1 else ''} today" if top else "Looking for inspiration")
        ),
    }

    return write_summary("content", data, day)


def _build_headline(
    all_items: list[Any],
    top: list[Any],
    waiting: list[Any],
) -> str:
    parts = [f"{len(all_items)} items in backlog"]
    if top:
        parts.append(f"top idea: {top[0].title[:40]}")
    if waiting:
        parts.append(f"{len(waiting)} drafts need review")
    return " — ".join(parts)
