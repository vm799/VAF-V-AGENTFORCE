"""Auto-classify raw braindump text into structured fields.

Uses keyword-based heuristics (no external APIs needed) to detect:
- thought_type: action / todo / idea / reflection / question / reference
- category: work / home / personal / health / finance / learning / creative
- priority: urgent / high / medium / low / someday
- linked_agents: which VAF agents this connects to
- tags: extracted keywords
"""

from __future__ import annotations

import re
from typing import Any


# ── Type detection ─────────────────────────────────────────────────────

_ACTION_WORDS = re.compile(
    r"\b(need to|must|should|have to|going to|will|do|fix|call|email|send|buy|book|schedule|submit|complete|finish|deliver|ship|deploy|push|build|create|write|prepare|set up|organise|organize)\b",
    re.IGNORECASE,
)
_QUESTION_WORDS = re.compile(r"\b(what|why|how|when|where|who|should i|could we|is it|can i|wonder)\b", re.IGNORECASE)
_TODO_MARKERS = re.compile(r"\b(todo|to-do|to do|reminder|don't forget|remember to)\b", re.IGNORECASE)
_IDEA_MARKERS = re.compile(r"\b(idea|maybe|what if|could be|concept|brainstorm|thought about|imagine|vision)\b", re.IGNORECASE)
_REFLECTION_MARKERS = re.compile(r"\b(realised|realized|learned|noticed|felt|feeling|grateful|proud|frustrated|worried|thinking about|reflecting)\b", re.IGNORECASE)

# ── Category detection ─────────────────────────────────────────────────

_WORK_KEYWORDS = re.compile(
    r"\b(work|office|meeting|client|manager|team|sprint|deadline|project|stakeholder|presentation|report|KPI|OKR|pipeline|deliverable|agentforce|promotion|career)\b",
    re.IGNORECASE,
)
_HOME_KEYWORDS = re.compile(
    r"\b(home|house|flat|apartment|garden|kitchen|clean|laundry|groceries|cook|shopping|DIY|repair|family|kids|children|school|nursery)\b",
    re.IGNORECASE,
)
_HEALTH_KEYWORDS = re.compile(
    r"\b(health|gym|workout|exercise|run|walk|steps|sleep|meditate|yoga|diet|weight|doctor|dentist|appointment|mental health|stress|anxiety|energy|water)\b",
    re.IGNORECASE,
)
_FINANCE_KEYWORDS = re.compile(
    r"\b(money|budget|savings|invest|stock|pension|tax|bill|rent|mortgage|salary|spend|expense|account|bank|ISA|crypto|portfolio)\b",
    re.IGNORECASE,
)
_LEARNING_KEYWORDS = re.compile(
    r"\b(learn|study|course|book|read|article|video|tutorial|podcast|research|understand|explore|skill|certificate|exam)\b",
    re.IGNORECASE,
)
_CREATIVE_KEYWORDS = re.compile(
    r"\b(content|write|blog|post|video|youtube|instagram|linkedin|create|design|art|music|photography|podcast|channel|audience)\b",
    re.IGNORECASE,
)

# ── Priority detection ─────────────────────────────────────────────────

_URGENT_MARKERS = re.compile(r"\b(urgent|asap|immediately|right now|critical|emergency|today|deadline today)\b", re.IGNORECASE)
_HIGH_MARKERS = re.compile(r"\b(important|high priority|this week|soon|before friday|by tomorrow|crucial)\b", re.IGNORECASE)
_LOW_MARKERS = re.compile(r"\b(whenever|no rush|low priority|at some point|eventually)\b", re.IGNORECASE)
_SOMEDAY_MARKERS = re.compile(r"\b(someday|one day|long term|future|maybe later|dream|aspirational)\b", re.IGNORECASE)

# ── Agent linkage ──────────────────────────────────────────────────────

AGENT_PATTERNS = {
    "finance": _FINANCE_KEYWORDS,
    "health": _HEALTH_KEYWORDS,
    "content": _CREATIVE_KEYWORDS,
    "education": _LEARNING_KEYWORDS,
}


def classify(raw_text: str) -> dict[str, Any]:
    """Classify raw braindump text into structured fields.

    Returns dict with: thought_type, category, priority, linked_agents, tags
    """
    text = raw_text.strip()

    # Detect type
    thought_type = _detect_type(text)

    # Detect category
    category = _detect_category(text)

    # Detect priority
    priority = _detect_priority(text)

    # Detect linked agents
    linked_agents = _detect_agents(text)

    # Extract tags (simple keyword extraction)
    tags = _extract_tags(text)

    # Generate title (first sentence or first 60 chars)
    title = _generate_title(text)

    return {
        "title": title,
        "thought_type": thought_type,
        "category": category,
        "priority": priority,
        "linked_agents": linked_agents,
        "tags": tags,
    }


def _detect_type(text: str) -> str:
    if _TODO_MARKERS.search(text):
        return "todo"
    if _QUESTION_WORDS.search(text) and text.rstrip().endswith("?"):
        return "question"
    if _REFLECTION_MARKERS.search(text):
        return "reflection"
    if _IDEA_MARKERS.search(text):
        return "idea"
    if _ACTION_WORDS.search(text):
        return "action"
    return "idea"


def _detect_category(text: str) -> str:
    scores: dict[str, int] = {}
    for cat, pattern in [
        ("work", _WORK_KEYWORDS),
        ("home", _HOME_KEYWORDS),
        ("health", _HEALTH_KEYWORDS),
        ("finance", _FINANCE_KEYWORDS),
        ("learning", _LEARNING_KEYWORDS),
        ("creative", _CREATIVE_KEYWORDS),
    ]:
        matches = pattern.findall(text)
        if matches:
            scores[cat] = len(matches)

    if not scores:
        return "personal"
    return max(scores, key=scores.get)


def _detect_priority(text: str) -> str:
    if _URGENT_MARKERS.search(text):
        return "urgent"
    if _HIGH_MARKERS.search(text):
        return "high"
    if _SOMEDAY_MARKERS.search(text):
        return "someday"
    if _LOW_MARKERS.search(text):
        return "low"
    return "medium"


def _detect_agents(text: str) -> list[str]:
    agents = []
    for agent, pattern in AGENT_PATTERNS.items():
        if pattern.search(text):
            agents.append(agent)
    return agents


def _extract_tags(text: str) -> list[str]:
    """Extract hashtags and key noun phrases."""
    tags: list[str] = []

    # Explicit #hashtags
    hashtags = re.findall(r"#(\w+)", text)
    tags.extend(h.lower() for h in hashtags)

    # Capitalised proper nouns (simple heuristic)
    words = text.split()
    for w in words:
        cleaned = re.sub(r"[^\w]", "", w)
        if cleaned and cleaned[0].isupper() and len(cleaned) > 2 and cleaned.lower() not in {
            "the", "and", "but", "for", "not", "you", "all", "can", "had", "her",
            "was", "one", "our", "out", "this", "that", "with", "have", "from",
            "they", "been", "said", "each", "which", "their", "will", "would",
            "could", "should", "need", "must", "about", "just", "also", "into",
        }:
            tags.append(cleaned.lower())

    return list(dict.fromkeys(tags))[:8]  # Dedupe, max 8 tags


def _generate_title(text: str) -> str:
    """Extract a concise title from the raw text."""
    # Use first sentence if short enough
    first_sentence = re.split(r"[.!?\n]", text)[0].strip()
    if len(first_sentence) <= 60:
        return first_sentence
    # Truncate to first 60 chars at a word boundary
    truncated = text[:60].rsplit(" ", 1)[0]
    return truncated + "..."
