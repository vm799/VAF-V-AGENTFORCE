"""Summarise education content — pure-text functions (no LLM calls).

These functions take pre-fetched text and return structured summaries,
entities, and topics using rule-based extraction. When run interactively
with Claude, these serve as the data structures that Claude fills in.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

# Common stop words to exclude from topic/entity extraction
_STOP_WORDS = frozenset(
    "a an the and or but in on at to for of is it by with from as are was were "
    "be been being have has had do does did will would shall should may might can "
    "could this that these those i you he she we they me him her us them my your "
    "his its our their what which who whom how when where why all each every some "
    "any no not so if than too very also just about up more out into over after".split()
)

# Known tech/finance/health entities to watch for
_KNOWN_ENTITIES = {
    "python", "javascript", "typescript", "react", "fastapi", "flask", "django",
    "ai", "ml", "llm", "gpt", "claude", "anthropic", "openai",
    "aws", "azure", "gcp", "docker", "kubernetes",
    "linkedin", "twitter", "youtube", "obsidian", "notion",
    "sqlite", "postgres", "redis", "mongodb",
    "finance", "investing", "budgeting", "savings",
    "health", "fitness", "sleep", "meditation", "running",
    "agentforce", "mcp", "langchain", "autogen",
}


@dataclass
class ContentSummary:
    """Summary of a single content item."""

    source_id: str
    title: str
    summary: str
    key_entities: list[str] = field(default_factory=list)
    key_topics: list[str] = field(default_factory=list)
    relevance_score: float = 0.0  # 0–1, how relevant to user's interests


@dataclass
class DaySummary:
    """Aggregated summary for a day's education content."""

    insights: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    top_entities: list[str] = field(default_factory=list)
    top_topics: list[str] = field(default_factory=list)
    items_processed: int = 0


def summarise_item(item_id: str, title: str, content: str) -> ContentSummary:
    """Produce a rule-based summary of a single content item."""
    # Extract first 2–3 meaningful sentences as summary
    sentences = _split_sentences(content)
    summary_text = " ".join(sentences[:3]) if sentences else title

    # Extract entities and topics
    entities = _extract_entities(content)
    topics = _extract_topics(title + " " + content)

    # Score relevance based on entity overlap with known interests
    relevance = len(set(entities) & _KNOWN_ENTITIES) / max(len(_KNOWN_ENTITIES), 1)
    relevance = min(relevance * 10, 1.0)  # Scale up

    return ContentSummary(
        source_id=item_id,
        title=title,
        summary=summary_text[:500],
        key_entities=entities[:10],
        key_topics=topics[:8],
        relevance_score=round(relevance, 2),
    )


def summarise_day(items: list[dict[str, Any]]) -> DaySummary:
    """Summarise all items for a day into aggregated insights."""
    summaries: list[ContentSummary] = []
    all_entities: list[str] = []
    all_topics: list[str] = []

    for item in items:
        s = summarise_item(
            item.get("id", ""),
            item.get("title", ""),
            item.get("content", ""),
        )
        summaries.append(s)
        all_entities.extend(s.key_entities)
        all_topics.extend(s.key_topics)

    # Rank by relevance
    summaries.sort(key=lambda s: s.relevance_score, reverse=True)

    # Top insights from highest-relevance items
    insights = [
        f"{s.title}: {s.summary[:120]}..."
        for s in summaries[:7]
        if s.summary
    ]

    # Generate next actions from top items
    next_actions = _generate_actions(summaries[:5])

    # Aggregate top entities and topics
    entity_counts = Counter(all_entities)
    topic_counts = Counter(all_topics)

    return DaySummary(
        insights=insights,
        next_actions=next_actions,
        top_entities=[e for e, _ in entity_counts.most_common(10)],
        top_topics=[t for t, _ in topic_counts.most_common(10)],
        items_processed=len(items),
    )


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, filtering out very short ones."""
    raw = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in raw if len(s.strip()) > 20]


def _extract_entities(text: str) -> list[str]:
    """Extract named entities using simple heuristics."""
    text_lower = text.lower()
    found: list[str] = []

    # Check against known entities
    for entity in _KNOWN_ENTITIES:
        if entity in text_lower:
            found.append(entity)

    # Find capitalised multi-word phrases (likely proper nouns)
    caps = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", text)
    for phrase in caps[:5]:
        normalised = phrase.lower()
        if normalised not in _STOP_WORDS and normalised not in found:
            found.append(normalised)

    return found


def _extract_topics(text: str) -> list[str]:
    """Extract topic keywords from text using frequency analysis."""
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    filtered = [w for w in words if w not in _STOP_WORDS and len(w) > 3]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(15)]


def _generate_actions(top_items: list[ContentSummary]) -> list[str]:
    """Generate simple next-action suggestions from top content items."""
    actions: list[str] = []
    for item in top_items:
        if not item.title:
            continue
        if any(e in ("python", "fastapi", "flask", "django", "react") for e in item.key_entities):
            actions.append(f"Try building something with concepts from: {item.title}")
        elif any(e in ("ai", "ml", "llm", "claude", "openai") for e in item.key_entities):
            actions.append(f"Deep-dive into AI topic: {item.title}")
        elif any(e in ("linkedin", "youtube") for e in item.key_entities):
            actions.append(f"Create content inspired by: {item.title}")
        else:
            actions.append(f"Review and note: {item.title}")

    return actions[:3]


def ai_summarise_item(item_id: str, title: str, content: str) -> ContentSummary:
    """Enhanced summarisation using LLM if available, falls back to keyword extraction.

    Only calls LLM if:
    - Content is > 500 chars (worth it)
    - An API key is configured (VAF_ANTHROPIC_KEY_1 or ANTHROPIC_API_KEY)
    - Falls back gracefully to existing keyword-based summarise_item() if LLM unavailable

    Args:
        item_id: Unique identifier for the content item.
        title: Title of the content.
        content: Full content text to summarise.

    Returns:
        ContentSummary with LLM-generated summary + entities/topics if available,
        otherwise keyword-extracted summary.
    """
    # Bail out early if content is too short or no LLM available
    if len(content) < 500:
        return summarise_item(item_id, title, content)

    try:
        from vaishali.core.llm_client import llm

        if not llm.has_keys():
            return summarise_item(item_id, title, content)

        # Build a concise prompt for LLM summarisation
        prompt = f"""Summarise this educational content in JSON format with these fields:
- summary (1-2 sentences, max 150 words)
- key_topics (list of 3-5 main topics)
- key_entities (list of 3-5 entities: tools, concepts, people, companies)
- relevance_score (0.0-1.0, how relevant to learning / tech / finance / health)

Content:
Title: {title}
{content[:1500]}

Return ONLY valid JSON, no markdown or extra text."""

        try:
            response = llm.complete(
                prompt=prompt,
                system="You are an expert content analyst. Extract key information from educational content.",
                max_tokens=200,
                agent="education",
                model="claude-haiku-4-5-20251001",
            )

            # Parse JSON response
            parsed = json.loads(response.content)

            return ContentSummary(
                source_id=item_id,
                title=title,
                summary=parsed.get("summary", "")[:500],
                key_entities=parsed.get("key_entities", [])[:10],
                key_topics=parsed.get("key_topics", [])[:8],
                relevance_score=min(max(float(parsed.get("relevance_score", 0.0)), 0.0), 1.0),
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # LLM response wasn't valid JSON, fall back
            log.warning(f"LLM summarisation for {item_id} failed ({e}), falling back to keyword extraction")
            return summarise_item(item_id, title, content)

    except ImportError:
        # LLM client not available, fall back
        return summarise_item(item_id, title, content)
    except Exception as e:
        # Any other error, log and fall back
        log.warning(f"LLM summarisation for {item_id} raised {type(e).__name__}: {e}, falling back")
        return summarise_item(item_id, title, content)
