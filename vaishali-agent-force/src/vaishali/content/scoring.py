"""Score and rank content ideas by effort vs impact and priority alignment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vaishali.content.backlog import ContentItem
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

EFFORT_WEIGHTS = {"S": 1.0, "M": 2.0, "L": 4.0}

# Priority themes — ideas matching these get a score boost
DEFAULT_PRIORITY_THEMES = [
    "ai", "finance", "career", "python", "content creation",
    "personal brand", "leadership", "health", "productivity",
]


@dataclass
class ScoredItem:
    """A content item with computed scores."""

    item: ContentItem
    roi_score: float  # impact / effort ratio
    priority_boost: float  # bonus for matching priority themes
    final_score: float  # Combined ranking score


def score_items(
    items: list[ContentItem],
    priority_themes: list[str] | None = None,
) -> list[ScoredItem]:
    """Score and rank content items.

    Scoring formula:
        roi = impact_estimate / effort_weight
        priority_boost = number of matching priority themes * 0.5
        final_score = roi + priority_boost
    """
    themes = [t.lower() for t in (priority_themes or DEFAULT_PRIORITY_THEMES)]
    scored: list[ScoredItem] = []

    for item in items:
        effort_w = EFFORT_WEIGHTS.get(item.effort_estimate, 2.0)
        roi = item.impact_estimate / effort_w

        # Check how many priority themes match the item's tags/title
        item_text = (item.title + " " + " ".join(item.tags)).lower()
        matches = sum(1 for theme in themes if theme in item_text)
        priority_boost = matches * 0.5

        final = round(roi + priority_boost, 2)

        scored.append(ScoredItem(
            item=item,
            roi_score=round(roi, 2),
            priority_boost=priority_boost,
            final_score=final,
        ))

    scored.sort(key=lambda s: s.final_score, reverse=True)
    return scored


def top_ideas(items: list[ContentItem], n: int = 5, priority_themes: list[str] | None = None) -> list[ContentItem]:
    """Return the top N ideas by score."""
    ranked = score_items(items, priority_themes)
    return [s.item for s in ranked[:n]]
