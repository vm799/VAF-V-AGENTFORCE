"""Content backlog CRUD over data/content/backlog.json."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

VALID_STATUSES = ("idea", "drafting", "needs_review", "ready", "published", "archived")
VALID_TYPES = ("linkedin", "long_form", "app_idea", "video_script", "childrens_book", "other")
VALID_EFFORTS = ("S", "M", "L")


@dataclass
class ContentItem:
    """A single content idea or draft in the backlog."""

    id: str = ""
    title: str = ""
    type: str = "other"  # linkedin, long_form, app_idea, video_script, etc.
    target_channel: str = ""
    status: str = "idea"
    effort_estimate: str = "M"  # S, M, L
    impact_estimate: int = 5  # 1–10
    source_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = uuid.uuid4().hex[:8]
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

    def validate(self) -> list[str]:
        errors = []
        if self.status not in VALID_STATUSES:
            errors.append(f"Invalid status '{self.status}'")
        if self.type not in VALID_TYPES:
            errors.append(f"Invalid type '{self.type}'")
        if self.effort_estimate not in VALID_EFFORTS:
            errors.append(f"Invalid effort '{self.effort_estimate}'")
        if not 1 <= self.impact_estimate <= 10:
            errors.append(f"Impact must be 1–10, got {self.impact_estimate}")
        return errors


def _backlog_path() -> Path:
    return settings.content_backlog_path


def load_backlog() -> list[ContentItem]:
    """Load the full content backlog from disk."""
    path = _backlog_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [ContentItem(**item) for item in data]
    except (json.JSONDecodeError, TypeError) as e:
        log.warning("Failed to load backlog: %s", e)
        return []


def save_backlog(items: list[ContentItem]) -> None:
    """Persist the full backlog to disk."""
    path = _backlog_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(i) for i in items], indent=2, default=str),
        encoding="utf-8",
    )
    log.info("Saved %d backlog items", len(items))


def add_item(item: ContentItem) -> ContentItem:
    """Add a new item to the backlog (validates first)."""
    errors = item.validate()
    if errors:
        raise ValueError(f"Invalid content item: {'; '.join(errors)}")
    items = load_backlog()
    items.append(item)
    save_backlog(items)
    log.info("Added backlog item: %s (%s)", item.title, item.id)
    return item


def update_item(item_id: str, **kwargs: Any) -> ContentItem | None:
    """Update an existing backlog item by ID."""
    items = load_backlog()
    for item in items:
        if item.id == item_id:
            for k, v in kwargs.items():
                if hasattr(item, k):
                    setattr(item, k, v)
            item.updated_at = datetime.utcnow().isoformat()
            errors = item.validate()
            if errors:
                raise ValueError(f"Invalid update: {'; '.join(errors)}")
            save_backlog(items)
            return item
    log.warning("Backlog item %s not found", item_id)
    return None


def delete_item(item_id: str) -> bool:
    """Remove an item from the backlog."""
    items = load_backlog()
    filtered = [i for i in items if i.id != item_id]
    if len(filtered) == len(items):
        return False
    save_backlog(filtered)
    log.info("Deleted backlog item: %s", item_id)
    return True


def list_by_status(status: str) -> list[ContentItem]:
    """Return all items with a given status."""
    return [i for i in load_backlog() if i.status == status]


def get_ideas() -> list[ContentItem]:
    """Return items in 'idea' status, sorted by impact descending."""
    ideas = list_by_status("idea")
    ideas.sort(key=lambda i: i.impact_estimate, reverse=True)
    return ideas


def get_drafts_waiting_review() -> list[ContentItem]:
    """Return items in 'needs_review' status."""
    return list_by_status("needs_review")
