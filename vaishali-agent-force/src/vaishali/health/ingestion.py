"""Ingest health data from daily summary files in data/health/raw/.

Expected CSV format (daily_YYYY-MM-DD.csv):
    date, steps, workout_minutes, sleep_hours, resting_hr, mood, energy,
    habits_completed, habits_total

Also supports a single JSON file with the same fields.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


@dataclass
class DailyMetrics:
    """Normalised daily health metrics."""

    date: str = ""
    steps: int = 0
    workout_minutes: int = 0
    sleep_hours: float = 0.0
    resting_hr: int = 0
    mood: int = 3  # 1–5
    energy: int = 3  # 1–5
    habits_completed: int = 0
    habits_total: int = 4

    @property
    def habit_rate(self) -> float:
        return self.habits_completed / max(self.habits_total, 1)


def load_daily_metrics(day: date | None = None) -> DailyMetrics | None:
    """Load metrics for a specific day from raw files."""
    day = day or date.today()
    raw_dir = settings.health_raw_dir

    # Try CSV first
    csv_path = raw_dir / f"daily_{day.isoformat()}.csv"
    if csv_path.exists():
        return _parse_csv(csv_path)

    # Try JSON
    json_path = raw_dir / f"daily_{day.isoformat()}.json"
    if json_path.exists():
        return _parse_json(json_path)

    log.warning("No health data found for %s", day)
    return None


def load_recent_metrics(days: int = 7) -> list[DailyMetrics]:
    """Load metrics for the last N days (most recent first)."""
    from datetime import timedelta

    today = date.today()
    results: list[DailyMetrics] = []

    for i in range(days):
        day = today - timedelta(days=i)
        m = load_daily_metrics(day)
        if m:
            results.append(m)

    return results


def save_daily_metrics(metrics: DailyMetrics) -> Path:
    """Save normalised daily metrics to the aggregated file."""
    agg_path = settings.data_dir / "health" / "daily_metrics.json"
    agg_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing
    existing: list[dict[str, Any]] = []
    if agg_path.exists():
        try:
            existing = json.loads(agg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []

    # Upsert by date
    existing = [e for e in existing if e.get("date") != metrics.date]
    existing.append(asdict(metrics))
    existing.sort(key=lambda e: e.get("date", ""))

    agg_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    log.info("Saved health metrics for %s", metrics.date)
    return agg_path


def _parse_csv(path: Path) -> DailyMetrics:
    """Parse a daily health CSV file."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            return DailyMetrics(
                date=row.get("date", ""),
                steps=_int(row.get("steps", 0)),
                workout_minutes=_int(row.get("workout_minutes", 0)),
                sleep_hours=_float(row.get("sleep_hours", 0)),
                resting_hr=_int(row.get("resting_hr", 0)),
                mood=_int(row.get("mood", 3)),
                energy=_int(row.get("energy", 3)),
                habits_completed=_int(row.get("habits_completed", 0)),
                habits_total=_int(row.get("habits_total", 4)),
            )
    return DailyMetrics()


def _parse_json(path: Path) -> DailyMetrics:
    """Parse a daily health JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list) and data:
        data = data[0]
    return DailyMetrics(
        date=data.get("date", ""),
        steps=_int(data.get("steps", 0)),
        workout_minutes=_int(data.get("workout_minutes", 0)),
        sleep_hours=_float(data.get("sleep_hours", 0)),
        resting_hr=_int(data.get("resting_hr", 0)),
        mood=_int(data.get("mood", 3)),
        energy=_int(data.get("energy", 3)),
        habits_completed=_int(data.get("habits_completed", 0)),
        habits_total=_int(data.get("habits_total", 4)),
    )


def _int(val: Any) -> int:
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def _float(val: Any) -> float:
    try:
        return round(float(val), 1)
    except (ValueError, TypeError):
        return 0.0
