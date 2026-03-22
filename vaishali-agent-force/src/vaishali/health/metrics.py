"""Compute health scores, detect streaks and deficits."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vaishali.core.logging_utils import get_logger
from vaishali.health.ingestion import DailyMetrics

log = get_logger(__name__)

# Targets (configurable later)
STEP_GOAL = 8000
SLEEP_GOAL_HOURS = 7.5
WORKOUT_GOAL_MINUTES = 30


@dataclass
class HealthScore:
    """Computed health assessment for a single day."""

    body_score: float  # 0–10
    movement_score: float  # 0–10
    sleep_score: float  # 0–10
    mood_energy_score: float  # 0–10
    habit_score: float  # 0–10
    comments: list[str]
    recommendation: str


def compute_body_score(metrics: DailyMetrics) -> HealthScore:
    """Compute a "body score" (0–10) from daily metrics.

    Weighted components:
        Movement (steps + workout): 30%
        Sleep: 30%
        Mood + Energy: 20%
        Habits: 20%
    """
    # Movement: steps + workout minutes
    step_ratio = min(metrics.steps / STEP_GOAL, 1.5)
    workout_ratio = min(metrics.workout_minutes / WORKOUT_GOAL_MINUTES, 1.5)
    movement = min((step_ratio * 6 + workout_ratio * 4), 10)

    # Sleep: 0–10 based on proximity to goal
    if metrics.sleep_hours <= 0:
        sleep = 0.0
    else:
        sleep_diff = abs(metrics.sleep_hours - SLEEP_GOAL_HOURS)
        sleep = max(10 - sleep_diff * 2, 0)

    # Mood + Energy: average scaled to 10
    mood_energy = ((metrics.mood + metrics.energy) / 2) * 2  # 1-5 → 2-10

    # Habits: completion rate × 10
    habits = metrics.habit_rate * 10

    # Weighted total
    body = round(movement * 0.3 + sleep * 0.3 + mood_energy * 0.2 + habits * 0.2, 1)
    body = min(max(body, 0), 10)

    # Comments
    comments = _generate_comments(metrics, movement, sleep, mood_energy, habits)
    recommendation = _generate_recommendation(metrics, movement, sleep, mood_energy)

    return HealthScore(
        body_score=body,
        movement_score=round(movement, 1),
        sleep_score=round(sleep, 1),
        mood_energy_score=round(mood_energy, 1),
        habit_score=round(habits, 1),
        comments=comments,
        recommendation=recommendation,
    )


def detect_streaks(recent_metrics: list[DailyMetrics]) -> dict[str, Any]:
    """Detect positive and negative streaks from recent data."""
    if not recent_metrics:
        return {"walk_streak": 0, "sleep_deficit_days": 0, "workout_streak": 0}

    walk_streak = 0
    workout_streak = 0
    sleep_deficit_days = 0

    for m in recent_metrics:  # Most recent first
        if m.steps >= STEP_GOAL:
            walk_streak += 1
        else:
            break

    for m in recent_metrics:
        if m.workout_minutes >= WORKOUT_GOAL_MINUTES:
            workout_streak += 1
        else:
            break

    for m in recent_metrics:
        if m.sleep_hours < SLEEP_GOAL_HOURS - 0.5:
            sleep_deficit_days += 1

    return {
        "walk_streak": walk_streak,
        "workout_streak": workout_streak,
        "sleep_deficit_days": sleep_deficit_days,
    }


def _generate_comments(
    m: DailyMetrics,
    movement: float,
    sleep: float,
    mood_energy: float,
    habits: float,
) -> list[str]:
    """Generate human-readable comments about the day's metrics."""
    comments: list[str] = []

    if m.steps >= STEP_GOAL:
        comments.append(f"Great movement — {m.steps:,} steps!")
    elif m.steps > 0:
        gap = STEP_GOAL - m.steps
        comments.append(f"{m.steps:,} steps — {gap:,} short of your {STEP_GOAL:,} goal.")

    if m.workout_minutes >= WORKOUT_GOAL_MINUTES:
        comments.append(f"{m.workout_minutes} min workout — solid session.")
    elif m.workout_minutes > 0:
        comments.append(f"{m.workout_minutes} min workout — aim for {WORKOUT_GOAL_MINUTES}+.")

    if m.sleep_hours >= SLEEP_GOAL_HOURS:
        comments.append(f"Good sleep: {m.sleep_hours}h.")
    elif m.sleep_hours > 0:
        comments.append(f"Sleep: {m.sleep_hours}h — below your {SLEEP_GOAL_HOURS}h target.")

    if m.habits_completed >= m.habits_total:
        comments.append(f"All {m.habits_total} habits completed!")
    elif m.habits_completed > 0:
        comments.append(f"{m.habits_completed}/{m.habits_total} habits completed.")

    return comments


def _generate_recommendation(
    m: DailyMetrics,
    movement: float,
    sleep: float,
    mood_energy: float,
) -> str:
    """Generate a single actionable recommendation."""
    # Prioritise the weakest area
    weakest = min(
        ("movement", movement),
        ("sleep", sleep),
        ("mood/energy", mood_energy),
        key=lambda x: x[1],
    )

    if weakest[0] == "sleep":
        return "Early night recommended — prioritise 7.5+ hours of sleep tonight."
    elif weakest[0] == "movement":
        if m.steps < STEP_GOAL // 2:
            return "Try a 30-minute walk today to boost your step count."
        return "Short walk + stretching recommended to hit your movement goal."
    else:
        if m.mood <= 2 or m.energy <= 2:
            return "Low energy/mood — consider a light walk, fresh air, and an early finish."
        return "Keep energy up with a short break and some movement this afternoon."
