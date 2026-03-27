"""Content idea generator — proposes new content from inputs.

Uses brain dump notes + education/research insights to generate ideas.
No LLM calls — pure Python logic that serves as the structure for
Claude-assisted generation when run interactively.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from vaishali.content.backlog import ContentItem
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

# Content type mapping based on topic/keyword signals
_TYPE_SIGNALS: dict[str, list[str]] = {
    "linkedin": ["career", "leadership", "networking", "professional", "job", "promotion", "salary"],
    "long_form": ["tutorial", "guide", "deep-dive", "analysis", "comparison", "review"],
    "video_script": ["demo", "walkthrough", "how-to", "show", "teach", "explain"],
    "app_idea": ["app", "tool", "build", "create", "saas", "product", "automate"],
}

# Channel mapping
_CHANNEL_MAP: dict[str, str] = {
    "linkedin": "LinkedIn",
    "long_form": "Blog / Medium",
    "video_script": "YouTube",
    "app_idea": "Product",
    "childrens_book": "Publishing",
    "other": "General",
}


def propose_ideas(
    brain_dumps: list[str] | None = None,
    education_insights: list[dict[str, Any]] | None = None,
    research_insights: list[dict[str, Any]] | None = None,
    max_ideas: int = 5,
) -> list[ContentItem]:
    """Generate content ideas from available inputs.

    Args:
        brain_dumps: Raw text from brain dump / journal markdown files.
        education_insights: Parsed insights from education summary JSON.
        research_insights: Parsed insights from research summary JSON.
        max_ideas: Maximum ideas to return.
    """
    raw_ideas: list[dict[str, Any]] = []

    # Extract ideas from brain dumps
    if brain_dumps:
        for text in brain_dumps:
            raw_ideas.extend(_ideas_from_text(text, source="brain_dump"))

    # Extract ideas from education insights
    if education_insights:
        for insight in education_insights:
            title = insight.get("title", "") or str(insight)
            entities = insight.get("key_entities", [])
            raw_ideas.append({
                "title": f"Post about: {title[:60]}",
                "source": "education",
                "entities": entities,
                "text": title,
            })

    # Extract ideas from research
    if research_insights:
        for item in research_insights:
            title = item.get("title", "")
            raw_ideas.append({
                "title": f"Research insight: {title[:60]}",
                "source": "research",
                "entities": item.get("tags", []),
                "text": title,
            })

    # Convert to ContentItems with type detection and scoring
    items: list[ContentItem] = []
    seen_titles: set[str] = set()

    for raw in raw_ideas:
        title = raw.get("title", "").strip()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)

        content_type = _detect_type(raw.get("text", "") + " " + title)
        source_ids = [raw["source"]] if "source" in raw else []

        item = ContentItem(
            id=hashlib.sha256(title.encode()).hexdigest()[:8],
            title=title,
            type=content_type,
            target_channel=_CHANNEL_MAP.get(content_type, "General"),
            status="idea",
            effort_estimate=_estimate_effort(content_type),
            impact_estimate=_estimate_impact(raw),
            source_ids=source_ids,
            tags=raw.get("entities", [])[:5],
        )
        items.append(item)

    # Sort by impact descending
    items.sort(key=lambda i: i.impact_estimate, reverse=True)
    return items[:max_ideas]


def load_brain_dumps(directory: Path) -> list[str]:
    """Read all Markdown files from a directory as brain dump text."""
    texts: list[str] = []
    if not directory.exists():
        return texts
    for md_file in sorted(directory.glob("*.md")):
        texts.append(md_file.read_text(encoding="utf-8"))
    return texts


def _ideas_from_text(text: str, source: str = "text") -> list[dict[str, Any]]:
    """Extract potential content ideas from free-form text."""
    ideas: list[dict[str, Any]] = []

    # Look for lines that start with idea-like patterns
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) < 10:
            continue

        # Lines starting with -, *, bullet, or "idea:"
        if re.match(r"^[-*•]\s+", line) or line.lower().startswith("idea:"):
            cleaned = re.sub(r"^[-*•]\s+|^idea:\s*", "", line, flags=re.IGNORECASE).strip()
            if len(cleaned) > 10:
                ideas.append({"title": cleaned[:80], "source": source, "text": cleaned, "entities": []})

    # If no bullet points found, use the first few sentences as a single idea
    if not ideas:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if sentences:
            title = sentences[0][:80]
            ideas.append({"title": title, "source": source, "text": text[:200], "entities": []})

    return ideas


def _detect_type(text: str) -> str:
    """Detect the best content type for the given text."""
    text_lower = text.lower()
    scores: dict[str, int] = {}

    for ctype, keywords in _TYPE_SIGNALS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[ctype] = score

    if scores:
        return max(scores, key=scores.get)  # type: ignore[arg-type]
    return "other"


def _estimate_effort(content_type: str) -> str:
    """Rough effort estimate by content type."""
    return {"linkedin": "S", "long_form": "L", "video_script": "L", "app_idea": "L"}.get(content_type, "M")


def _estimate_impact(raw: dict[str, Any]) -> int:
    """Score impact 1–10 based on signals."""
    score = 5  # Base
    entities = raw.get("entities", [])

    # Boost for trending/high-value topics
    high_value = {"ai", "llm", "claude", "python", "react", "finance", "health"}
    overlap = len(set(e.lower() for e in entities) & high_value)
    score += min(overlap * 2, 4)

    # Boost for education-sourced ideas (validated by learning)
    if raw.get("source") == "education":
        score += 1

    return min(score, 10)
