"""Generate daily braindump summary for the dashboard."""

from __future__ import annotations

from datetime import date
from typing import Any

from vaishali.braindump.storage import get_active_actions, get_stats, get_today_thoughts
from vaishali.core.logging_utils import get_logger
from vaishali.core.summaries import write_summary

log = get_logger(__name__)


def generate_summary(day: date | None = None) -> dict[str, Any]:
    """Build today's braindump summary and write to disk."""
    day = day or date.today()

    stats = get_stats()
    today_thoughts = get_today_thoughts()
    active = get_active_actions()

    # Derive status/mood
    status, mood = _derive_status_mood(stats, today_thoughts)

    # Build headline
    if today_thoughts:
        headline = f"{len(today_thoughts)} new thoughts captured today"
    elif stats["total"] > 0:
        headline = f"{stats['active_actions']} actions pending"
    else:
        headline = "No thoughts captured yet — try /dump"

    # Recent thoughts for display
    recent = [
        {
            "id": t.id,
            "title": t.title,
            "type": t.thought_type,
            "category": t.category,
            "priority": t.priority,
            "when": t.when,
            "status": t.status,
        }
        for t in today_thoughts[:10]
    ]

    # Top actions
    top_actions = [
        {
            "id": a.id,
            "title": a.title,
            "priority": a.priority,
            "category": a.category,
            "when": a.when,
        }
        for a in active[:5]
    ]

    summary: dict[str, Any] = {
        "date": day.isoformat(),
        "headline": headline,
        "status": status,
        "mood": mood,
        "total_thoughts": stats["total"],
        "today_count": stats["today"],
        "active_actions": stats["active_actions"],
        "by_category": stats["by_category"],
        "by_priority": stats["by_priority"],
        "recent_thoughts": recent,
        "top_actions": top_actions,
    }

    write_summary("braindump", summary, day)
    log.info("Braindump summary generated: %s", headline)
    return summary


def _derive_status_mood(stats: dict, today_thoughts: list) -> tuple[str, str]:
    """Derive agent status and mood from braindump data."""
    active = stats["active_actions"]
    today = stats["today"]
    urgent = stats.get("by_priority", {}).get("urgent", 0)

    if urgent > 0:
        return "warning", f"{urgent} urgent item{'s' if urgent > 1 else ''} need attention"
    if today >= 5:
        return "success", "Brain is flowing — great capture session!"
    if today > 0:
        return "success", f"{today} thought{'s' if today > 1 else ''} captured today"
    if active > 0:
        return "idle", f"{active} action{'s' if active > 1 else ''} waiting"
    return "idle", "Ready to capture your thoughts"
