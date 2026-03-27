"""url_queue.py — Persist incoming URLs for batched NLM processing.

All links dropped in Telegram are queued here.
The 8pm daily batch job reads this queue, runs NLM, and updates insights.

Queue file: data/education/nlm_queue.json
Each entry: {id, url, title, category, insight_id, queued_at, status}
  status: pending | processing | done | failed
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

Status = Literal["pending", "processing", "done", "failed"]

QUEUE_FILE = settings.data_dir / "education" / "nlm_queue.json"


def _load() -> list[dict]:
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text())
        except Exception:
            return []
    return []


def _save(items: list[dict]) -> None:
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False))


def enqueue(url: str, title: str, category: str, insight_id: str) -> dict:
    """Add a URL to the NLM processing queue. Skips if already queued."""
    items = _load()

    # Skip duplicates
    if any(item["url"] == url for item in items):
        log.info("URL already queued: %s", url[:60])
        return next(i for i in items if i["url"] == url)

    entry = {
        "id": f"q_{abs(hash(url)) % 1_000_000:06d}",
        "url": url,
        "title": title[:120],
        "category": category,
        "insight_id": insight_id,
        "queued_at": datetime.now().isoformat(),
        "status": "pending",
        "nlm_summary": "",
        "error": "",
    }
    items.append(entry)
    _save(items)
    log.info("Queued for NLM: %s", url[:60])
    return entry


def get_pending() -> list[dict]:
    """Return all pending queue entries."""
    return [i for i in _load() if i.get("status") == "pending"]


def get_all() -> list[dict]:
    """Return all queue entries, newest first."""
    return sorted(_load(), key=lambda x: x.get("queued_at", ""), reverse=True)


def mark_done(url: str, nlm_summary: str) -> None:
    items = _load()
    for item in items:
        if item["url"] == url:
            item["status"] = "done"
            item["nlm_summary"] = nlm_summary
            item["processed_at"] = datetime.now().isoformat()
    _save(items)


def mark_failed(url: str, error: str) -> None:
    items = _load()
    for item in items:
        if item["url"] == url:
            item["status"] = "failed"
            item["error"] = error[:200]
    _save(items)


def pending_count() -> int:
    return len(get_pending())


def queue_summary() -> str:
    """One-line summary for Telegram confirmation."""
    items = _load()
    pending = sum(1 for i in items if i["status"] == "pending")
    done = sum(1 for i in items if i["status"] == "done")
    total = len(items)
    return f"{total} total · {pending} pending NLM · {done} processed"
