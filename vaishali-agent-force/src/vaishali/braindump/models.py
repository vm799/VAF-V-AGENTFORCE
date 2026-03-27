"""Data models for the braindump agent."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


VALID_CATEGORIES = ("work", "home", "personal", "health", "finance", "learning", "creative")
VALID_PRIORITIES = ("urgent", "high", "medium", "low", "someday")
VALID_TYPES = ("action", "todo", "idea", "reflection", "question", "reference")
VALID_STATUSES = ("captured", "processed", "actioned", "archived", "discarded")


@dataclass
class Thought:
    """A single captured thought/braindump entry."""

    id: str = ""
    raw_text: str = ""
    title: str = ""                     # Derived short title
    thought_type: str = "idea"          # action, todo, idea, reflection, question, reference
    category: str = "personal"          # work, home, personal, health, finance, learning, creative
    priority: str = "medium"            # urgent, high, medium, low, someday
    why: str = ""                       # Why this matters
    when: str = ""                      # Deadline or timeframe (freeform: "this week", "2026-03-25", "someday")
    tags: list[str] = field(default_factory=list)
    linked_agents: list[str] = field(default_factory=list)  # finance, content, education, health
    obsidian_path: str = ""             # Path to the generated Obsidian note
    status: str = "captured"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"bd-{uuid.uuid4().hex[:8]}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        if not self.title and self.raw_text:
            self.title = self.raw_text[:60].strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "raw_text": self.raw_text,
            "title": self.title,
            "thought_type": self.thought_type,
            "category": self.category,
            "priority": self.priority,
            "why": self.why,
            "when": self.when,
            "tags": self.tags,
            "linked_agents": self.linked_agents,
            "obsidian_path": self.obsidian_path,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Thought:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.thought_type not in VALID_TYPES:
            errors.append(f"Invalid type '{self.thought_type}'")
        if self.category not in VALID_CATEGORIES:
            errors.append(f"Invalid category '{self.category}'")
        if self.priority not in VALID_PRIORITIES:
            errors.append(f"Invalid priority '{self.priority}'")
        if self.status not in VALID_STATUSES:
            errors.append(f"Invalid status '{self.status}'")
        if not self.raw_text:
            errors.append("raw_text is required")
        return errors
