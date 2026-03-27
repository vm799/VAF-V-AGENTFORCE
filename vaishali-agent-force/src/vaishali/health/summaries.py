"""Generate daily health summary JSON."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from vaishali.core.logging_utils import get_logger
from vaishali.core.summaries import write_summary
from vaishali.health.ingestion import (
    DailyMetrics,
    load_daily_metrics,
    load_recent_metrics,
    save_daily_metrics,
)
from vaishali.health.metrics import compute_body_score, detect_streaks

log = get_logger(__name__)


def generate_daily_summary(day: date | None = None) -> Path:
    """Write data/summaries/health/YYYY-MM-DD.json."""
    day = day or date.today()

    metrics = load_daily_metrics(day)
    if not metrics:
        # No data — write a placeholder summary
        data: dict[str, Any] = {
            "date": day.isoformat(),
            "agent": "health",
            "body_score": None,
            "movement": None,
            "sleep": None,
            "habits": None,
            "comments": [],
            "recommendation": "No health data for today — log your daily check-in.",
            "headline": "No health data recorded.",
            "status": "idle",
            "mood": "Log your daily check-in",
        }
        return write_summary("health", data, day)

    # Persist aggregated metrics
    save_daily_metrics(metrics)

    # Compute scores
    score = compute_body_score(metrics)

    # Detect streaks from recent data
    recent = load_recent_metrics(days=7)
    streaks = detect_streaks(recent)

    # Build headline
    headline = (
        f"Body: {score.body_score}/10 — "
        f"{metrics.steps:,} steps, {metrics.workout_minutes}min workout, "
        f"{metrics.sleep_hours}h sleep, energy {metrics.energy}/5, "
        f"{metrics.habits_completed}/{metrics.habits_total} habits"
    )

    data = {
        "date": day.isoformat(),
        "agent": "health",
        "body_score": score.body_score,
        "movement": {
            "steps": metrics.steps,
            "workout_minutes": metrics.workout_minutes,
            "score": score.movement_score,
        },
        "sleep": {
            "hours": metrics.sleep_hours,
            "resting_hr": metrics.resting_hr,
            "score": score.sleep_score,
        },
        "mood_energy": {
            "mood": metrics.mood,
            "energy": metrics.energy,
            "score": score.mood_energy_score,
        },
        "habits": {
            "completed": metrics.habits_completed,
            "total": metrics.habits_total,
            "rate": round(metrics.habit_rate, 2),
            "score": score.habit_score,
        },
        "streaks": streaks,
        "comments": score.comments,
        "recommendation": score.recommendation,
        "headline": headline,
        "status": "warning" if score.body_score < 5 else "success",
        "mood": (
            "Feeling great!" if score.body_score >= 8
            else "Doing okay — keep moving" if score.body_score >= 5
            else "Needs attention today"
        ),
    }

    return write_summary("health", data, day)
