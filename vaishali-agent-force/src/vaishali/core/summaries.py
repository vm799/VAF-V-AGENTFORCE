"""Shared utilities for reading/writing agent summary JSON files."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

AGENTS = ("finance", "content", "education", "research", "health", "braindump")


def summary_path(agent: str, day: date | None = None) -> Path:
    day = day or date.today()
    return settings.summaries_dir / agent / f"{day.isoformat()}.json"


def write_summary(agent: str, data: dict[str, Any], day: date | None = None) -> Path:
    path = summary_path(agent, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    log.info("Wrote %s summary → %s", agent, path.name)
    return path


def read_summary(agent: str, day: date | None = None) -> dict[str, Any] | None:
    path = summary_path(agent, day)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_all_summaries(day: date | None = None) -> dict[str, dict[str, Any] | None]:
    return {agent: read_summary(agent, day) for agent in AGENTS}
