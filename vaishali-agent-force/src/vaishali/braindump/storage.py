"""CRUD operations for braindump thoughts over data/braindump/thoughts.json."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from vaishali.braindump.models import Thought
from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


def _thoughts_path():
    return settings.braindump_dir / "thoughts.json"


def load_thoughts() -> list[Thought]:
    """Load all thoughts from disk."""
    path = _thoughts_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [Thought.from_dict(item) for item in data]
    except (json.JSONDecodeError, TypeError) as e:
        log.warning("Failed to load thoughts: %s", e)
        return []


def save_thoughts(thoughts: list[Thought]) -> None:
    """Persist all thoughts to disk."""
    path = _thoughts_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([t.to_dict() for t in thoughts], indent=2, default=str),
        encoding="utf-8",
    )
    log.info("Saved %d thoughts", len(thoughts))


def add_thought(thought: Thought) -> Thought:
    """Add a new thought (validates first)."""
    errors = thought.validate()
    if errors:
        raise ValueError(f"Invalid thought: {'; '.join(errors)}")
    thoughts = load_thoughts()
    thoughts.append(thought)
    save_thoughts(thoughts)
    log.info("Added thought: %s (%s)", thought.title, thought.id)
    return thought


def update_thought(thought_id: str, **kwargs: Any) -> Thought | None:
    """Update an existing thought by ID."""
    thoughts = load_thoughts()
    for t in thoughts:
        if t.id == thought_id:
            for k, v in kwargs.items():
                if hasattr(t, k):
                    setattr(t, k, v)
            t.updated_at = datetime.utcnow().isoformat()
            errors = t.validate()
            if errors:
                raise ValueError(f"Invalid update: {'; '.join(errors)}")
            save_thoughts(thoughts)
            return t
    return None


def get_today_thoughts() -> list[Thought]:
    """Return thoughts created today."""
    today = date.today().isoformat()
    return [t for t in load_thoughts() if t.created_at.startswith(today)]


def get_by_category(category: str) -> list[Thought]:
    """Return all thoughts in a given category."""
    return [t for t in load_thoughts() if t.category == category]


def get_active_actions() -> list[Thought]:
    """Return unactioned todos and actions, sorted by priority."""
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3, "someday": 4}
    active = [
        t for t in load_thoughts()
        if t.thought_type in ("action", "todo") and t.status in ("captured", "processed")
    ]
    active.sort(key=lambda t: priority_order.get(t.priority, 5))
    return active


def get_stats() -> dict[str, Any]:
    """Return aggregate statistics for the braindump."""
    thoughts = load_thoughts()
    today = date.today().isoformat()
    today_count = sum(1 for t in thoughts if t.created_at.startswith(today))

    by_category: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_status: dict[str, int] = {}

    for t in thoughts:
        by_category[t.category] = by_category.get(t.category, 0) + 1
        by_type[t.thought_type] = by_type.get(t.thought_type, 0) + 1
        by_priority[t.priority] = by_priority.get(t.priority, 0) + 1
        by_status[t.status] = by_status.get(t.status, 0) + 1

    return {
        "total": len(thoughts),
        "today": today_count,
        "by_category": by_category,
        "by_type": by_type,
        "by_priority": by_priority,
        "by_status": by_status,
        "active_actions": len(get_active_actions()),
    }
