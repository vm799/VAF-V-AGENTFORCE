"""Generate daily education summary JSON."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger
from vaishali.core.summaries import write_summary
from vaishali.education.graph_builder import load_graph, save_graph, update_graph
from vaishali.education.summariser import summarise_day, summarise_item

log = get_logger(__name__)


def generate_daily_summary(day: date | None = None) -> Path:
    """Generate the daily education summary from today's raw items.

    1. Load raw items from notes dir.
    2. Summarise each item and the day overall.
    3. Update the knowledge graph.
    4. Write the summary JSON.
    """
    day = day or date.today()

    # Load raw items
    raw_path = settings.data_dir / "education" / "notes" / f"{day.isoformat()}_raw.json"
    if not raw_path.exists():
        log.warning("No raw education items for %s", day)
        data: dict[str, Any] = {
            "date": day.isoformat(),
            "agent": "education",
            "new_insights": [],
            "next_actions": [],
            "items_processed": 0,
            "headline": "No new education content today.",
            "status": "idle",
            "mood": "Ready to learn",
        }
        return write_summary("education", data, day)

    items = json.loads(raw_path.read_text(encoding="utf-8"))

    # Summarise
    day_summary = summarise_day(items)

    # Update knowledge graph
    item_summaries = [
        asdict(summarise_item(i.get("id", ""), i.get("title", ""), i.get("content", "")))
        for i in items
    ]
    graph = load_graph()
    graph = update_graph(graph, items, item_summaries)
    save_graph(graph)

    # Build summary
    headline_parts = [f"{day_summary.items_processed} items processed"]
    if day_summary.top_topics:
        headline_parts.append(f"top topics: {', '.join(day_summary.top_topics[:3])}")
    headline = " — ".join(headline_parts)

    data = {
        "date": day.isoformat(),
        "agent": "education",
        "new_insights": day_summary.insights,
        "next_actions": day_summary.next_actions,
        "top_entities": day_summary.top_entities,
        "top_topics": day_summary.top_topics,
        "items_processed": day_summary.items_processed,
        "headline": headline,
        "status": "success" if day_summary.items_processed > 0 else "idle",
        "mood": (
            f"Processed {day_summary.items_processed} item{'s' if day_summary.items_processed > 1 else ''} today"
            if day_summary.items_processed > 0
            else "Ready to learn"
        ),
    }

    return write_summary("education", data, day)
