"""insight_writer.py — Extract structured insights from any URL, route to Obsidian by content type.

Full pipeline:
  URL → classify content type → Claude extracts insights
      → save JSON in data/education/notes/insights/{category}/
      → write Obsidian note to correct vault section (vault/Recipes/, vault/Finance/, etc.)
      → optionally enrich with NotebookLM via notebooklm_client (if configured)

Obsidian vault routing by category:
  recipe   → {vault}/Personal/Recipes/
  finance  → {vault}/Finance/Research/
  ai       → {vault}/Research/AI/
  tech     → {vault}/Research/Technology/
  health   → {vault}/Health/
  career   → {vault}/Professional/Career/
  education→ {vault}/Education/
  research → {vault}/Research/
  personal → {vault}/Personal/
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

# Maps category → (vault subfolder, display label, emoji)
CATEGORY_VAULT_MAP: dict[str, tuple[str, str, str]] = {
    "recipe":    ("Personal/Recipes",    "Recipes",     "🍳"),
    "finance":   ("Finance/Research",    "Finance",     "💰"),
    "ai":        ("Research/AI",         "AI & ML",     "🤖"),
    "tech":      ("Research/Technology", "Technology",  "💻"),
    "health":    ("Health",              "Health",      "🏃"),
    "career":    ("Professional/Career", "Career",      "🎯"),
    "personal":  ("Personal",            "Personal",    "📝"),
    "education": ("Education",           "Education",   "📚"),
    "research":  ("Research",            "Research",    "🔬"),
}

# Category-specific Claude prompts — tailored to what's actually useful per type
_PROMPTS: dict[str, str] = {
    "recipe": """Extract structured information from this recipe.

Return ONLY valid JSON:
{{
  "summary": "One sentence: what dish, key technique, why make it",
  "key_insights": ["key ingredient or technique", "prep tip", "variation idea"],
  "key_topics": ["cuisine type", "meal type", "dietary tag"],
  "key_entities": ["key ingredient 1", "key ingredient 2"],
  "action_items": ["Try this recipe on [day/occasion]"],
  "relevance": "Quick personal note on appeal",
  "quality_score": 7
}}

Title: {title}
URL: {url}
Content: {content}""",

    "finance": """You are a senior asset management analyst. Extract investment-relevant insights.

Return ONLY valid JSON:
{{
  "summary": "2-3 sentences: what this means for markets/portfolios/asset management",
  "key_insights": ["market implication 1", "risk/opportunity", "data point"],
  "key_topics": ["asset class", "market theme", "instrument type"],
  "key_entities": ["company/fund/index name"],
  "action_items": ["portfolio action or further research step"],
  "relevance": "Why this matters for an asset management professional in 2026",
  "quality_score": 7
}}

Title: {title}
URL: {url}
Content: {content}""",

    "default": """You are an expert analyst. Extract structured insights from this content.

Return ONLY valid JSON:
{{
  "summary": "2-3 sentence summary of what this is and why it matters",
  "key_insights": ["key takeaway 1", "key takeaway 2", "key takeaway 3"],
  "key_topics": ["topic1", "topic2", "topic3"],
  "key_entities": ["person/org/product mentioned"],
  "action_items": ["one concrete next step based on this content"],
  "relevance": "Why this is relevant to Vaishali — asset management professional and AI builder",
  "quality_score": 7
}}

quality_score: 1-10. key_insights: 3-5 full sentences. No line breaks inside JSON values.

Title: {title}
URL: {url}
Content: {content}""",
}


@dataclass
class Insight:
    id: str
    title: str
    url: str
    summary: str
    category: str = "research"
    key_insights: list[str] = field(default_factory=list)
    key_topics: list[str] = field(default_factory=list)
    key_entities: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    relevance: str = ""
    quality_score: int = 5
    source: str = "telegram"
    notebooklm_summary: str = ""   # enriched by NLM if available
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def vault_folder(self) -> str:
        return CATEGORY_VAULT_MAP.get(self.category, ("Research", "Research", "🔬"))[0]

    @property
    def category_label(self) -> str:
        return CATEGORY_VAULT_MAP.get(self.category, ("Research", "Research", "🔬"))[1]

    @property
    def emoji(self) -> str:
        return CATEGORY_VAULT_MAP.get(self.category, ("Research", "Research", "🔬"))[2]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_obsidian_markdown(self) -> str:
        """Render as Obsidian-compatible markdown with YAML frontmatter."""
        tag_yaml = ", ".join(f'"{t}"' for t in self.key_topics[:8])
        topic_links = " ".join(f"[[{t}]]" for t in self.key_topics[:6])
        entities_str = ", ".join(self.key_entities[:5]) if self.key_entities else "—"
        insights_md = "\n".join(f"- {i}" for i in self.key_insights)
        actions_md = "\n".join(f"- [ ] {a}" for a in self.action_items) if self.action_items else "- None"
        nlm_section = f"\n## NotebookLM Summary\n\n{self.notebooklm_summary}\n" if self.notebooklm_summary else ""

        return f"""---
title: "{self.title.replace('"', "'")}"
url: {self.url}
date: {self.created_at[:10]}
category: {self.category}
tags: [{tag_yaml}]
quality: {self.quality_score}
source: {self.source}
---

## Summary

{self.summary}
{nlm_section}
## Key Insights

{insights_md}

## Topics & Entities

**Topics:** {topic_links}
**Entities:** {entities_str}

## Why It Matters

{self.relevance}

## Action Items

{actions_md}

---
*{self.emoji} Captured via Vaishali Agent Force · {self.created_at[:10]}*
"""


async def extract_insights(title: str, url: str, content: str, category: str = "research") -> Insight:
    """Extract structured insights using Gemini (primary, free) or Claude (fallback).

    Priority:
      1. Google Gemini 1.5 Flash — if VAF_GOOGLE_AI_KEY set in .env (free, fast)
      2. Claude via Anthropic     — if ANTHROPIC_API_KEY set in .env
      3. Sentence-extract fallback — saves a useful stub without AI
    """
    insight_id = f"ins_{date.today().isoformat()}_{abs(hash(url)) % 100000:05d}"

    if not content or len(content) < 80:
        return Insight(
            id=insight_id, title=title, url=url, category=category,
            summary="Content too short to extract insights — link saved for manual review.",
        )

    prompt_template = _PROMPTS.get(category, _PROMPTS["default"])
    prompt = prompt_template.format(title=title, url=url, content=content[:4000])
    system = "Return valid JSON only. No markdown code fences. No extra text."

    raw: str | None = None
    provider_used: str = "none"

    # ── 1. Try Gemini (Google free tier) ─────────────────────────────
    try:
        from vaishali.core.gemini_client import gemini
        if gemini.has_key():
            raw = await gemini.complete_async(prompt=prompt, system=system, max_tokens=900)
            provider_used = "gemini"
            log.info("Insights extracted via Gemini for: %s", title[:50])
    except Exception as e:
        log.warning("Gemini insight extraction failed: %s", e)
        raw = None

    # ── 2. Try Claude (Anthropic) ─────────────────────────────────────
    if raw is None:
        try:
            from vaishali.core.llm_client import llm
            if llm.has_keys():
                response = await llm.complete_async(prompt=prompt, system=system, max_tokens=900)
                raw = response.content.strip()
                provider_used = "claude"
                log.info("Insights extracted via Claude for: %s", title[:50])
        except Exception as e:
            log.warning("Claude insight extraction failed: %s", e)
            raw = None

    # ── 3. Parse LLM response ─────────────────────────────────────────
    if raw:
        try:
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
            data = json.loads(cleaned)
            return Insight(
                id=insight_id, title=title, url=url, category=category,
                summary=data.get("summary", ""),
                key_insights=data.get("key_insights", []),
                key_topics=data.get("key_topics", []),
                key_entities=data.get("key_entities", []),
                action_items=data.get("action_items", []),
                relevance=data.get("relevance", ""),
                quality_score=int(data.get("quality_score", 5)),
            )
        except Exception as e:
            log.warning("Failed to parse %s response as JSON: %s", provider_used, e)

    # ── 4. Fallback: sentence extract (no AI required) ────────────────
    log.info("Using sentence-extract fallback for: %s", title[:50])
    sentences = [s.strip() for s in content.replace("\n", " ").split(".") if len(s.strip()) > 30]
    auto_summary = ". ".join(sentences[:3]) + "." if sentences else title
    no_ai_hint = (
        "Add VAF_GOOGLE_AI_KEY to .env for free AI analysis (https://aistudio.google.com/apikey)"
    )
    return Insight(
        id=insight_id, title=title, url=url, category=category,
        summary=auto_summary[:400],
        key_insights=[no_ai_hint],
        key_topics=[category],
        relevance="Saved without AI analysis — see key_insights for setup instructions.",
        quality_score=3,
    )


def save_insight_json(insight: Insight) -> Path:
    """Persist insight JSON in data/education/notes/insights/{category}/."""
    dest = settings.data_dir / "education" / "notes" / "insights" / insight.category
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{insight.id}.json"
    path.write_text(json.dumps(insight.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Saved %s insight: %s", insight.category, insight.title[:50])
    return path


def write_obsidian_note(insight: Insight) -> Path | None:
    """Write markdown note to the correct Obsidian vault section.

    Routes by insight.category:
      recipe   → {vault}/Personal/Recipes/
      finance  → {vault}/Finance/Research/
      ai       → {vault}/Research/AI/
      tech     → {vault}/Research/Technology/
      health   → {vault}/Health/
      career   → {vault}/Professional/Career/
      etc.

    Set VAF_OBSIDIAN_VAULT_DIR in .env to enable.
    """
    if not settings.obsidian_vault_dir:
        return None

    vault = Path(settings.obsidian_vault_dir)
    if not vault.exists():
        log.warning("Obsidian vault not found at %s — skipping note", vault)
        return None

    note_dir = vault / insight.vault_folder
    note_dir.mkdir(parents=True, exist_ok=True)

    safe_name = re.sub(r'[^\w\s\-]', '', insight.title)[:60].strip()
    safe_name = re.sub(r'\s+', '_', safe_name)
    note_path = note_dir / f"{safe_name}.md"

    note_path.write_text(insight.to_obsidian_markdown(), encoding="utf-8")
    log.info("Obsidian note → %s/%s.md", insight.vault_folder, safe_name)
    return note_path


def load_recent_insights(limit: int = 20, category: str | None = None) -> list[dict[str, Any]]:
    """Load recent insights from JSON store, newest first.

    Pass category to filter (e.g. 'finance', 'recipe'). None returns all.
    """
    base = settings.data_dir / "education" / "notes" / "insights"
    if not base.exists():
        return []

    if category:
        glob_path = base / category
        files = sorted(glob_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if glob_path.exists() else []
    else:
        files = sorted(base.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    results = []
    for f in files[:limit]:
        try:
            results.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return results
