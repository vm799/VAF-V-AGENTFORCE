"""Orchestrator — the brain of the golden thread.

Routes raw content (thoughts, URLs, statements, brain dumps) through the
correct agent's intelligence, enriching it with structured insights, revenue
angles, and Obsidian-ready frontmatter BEFORE writing to storage.

Pipeline:  Input → detect_agent → load SKILL.md → Claude Haiku enrich → structured output

Usage:
    from vaishali.orchestrator import orchestrate

    result = orchestrate("Just read about LangGraph parallel fan-out — could speed up morning pipeline 3x")
    # result.agent = "FORGE"
    # result.title = "LangGraph Parallel Fan-Out for Morning Pipeline"
    # result.insights = ["3x speed improvement possible", ...]
    # result.revenue_angle = "💰 Build → teach → portfolio → consulting"
    # result.signal_rating = "🟢"
    # result.enriched_content = "..."  (full structured note)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vaishali.captures.store import VAULT_PATH_MAP, detect_agent, detect_revenue_angle
from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

# ── Agent SKILL.md paths ─────────────────────────────────────────────

# Look for agent files in the Claude Project directory first, then fallback
_AGENT_DIRS = [
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "V-AgentForce-Project" / "agents",
    settings.base_dir / "agents",
]

AGENT_FILE_MAP: dict[str, str] = {
    "SENTINEL": "00_SENTINEL.md",
    "FORGE":    "01_FORGE.md",
    "AMPLIFY":  "02_AMPLIFY.md",
    "PHOENIX":  "03_PHOENIX.md",
    "VITALITY": "04_VITALITY.md",
    "CIPHER":   "05_CIPHER.md",
    "AEGIS":    "06_AEGIS.md",
    "NEXUS":    "07_NEXUS.md",
    "ATLAS":    "08_ATLAS.md",
    "COLOSSUS": "09_COLOSSUS.md",
}


def _load_agent_prompt(agent: str) -> str:
    """Load agent's SKILL.md file as system context. Returns empty string if not found."""
    filename = AGENT_FILE_MAP.get(agent, "")
    if not filename:
        return ""
    for agent_dir in _AGENT_DIRS:
        path = agent_dir / filename
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                log.warning("Failed to read agent file: %s", path)
    return ""


# ── Enrichment output ─────────────────────────────────────────────────

@dataclass
class EnrichedCapture:
    """Structured output from the orchestrator."""

    agent: str
    title: str
    summary: str
    insights: list[str]
    revenue_angle: str
    signal_rating: str  # 🟢 must-act | 🟡 valuable | 🔴 noise
    tags: list[str]
    enriched_content: str  # Full structured note for Obsidian
    source_url: str = ""
    url_summary: str = ""  # If input was a URL, the page summary
    raw_input: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "title": self.title,
            "summary": self.summary,
            "insights": self.insights,
            "revenue_angle": self.revenue_angle,
            "signal_rating": self.signal_rating,
            "tags": self.tags,
            "enriched_content": self.enriched_content,
            "source_url": self.source_url,
            "url_summary": self.url_summary,
        }


# ── Enrichment prompt ─────────────────────────────────────────────────

_ENRICHMENT_PROMPT = """You are {agent}, part of V AgentForce — an elite squad of AI agents working for V (Vaishali Mehmi), a senior finance professional building an AI empire.

Your job: take this raw input from V and enrich it into a structured intelligence note.

RAW INPUT:
{content}

{url_context}

Respond in EXACTLY this JSON format (no markdown, no code fences, just raw JSON):
{{
  "title": "A clear, specific title (max 80 chars)",
  "summary": "2-3 sentence summary of what this is and why it matters to V",
  "insights": ["insight 1", "insight 2", "insight 3"],
  "revenue_angle": "Specific way V can monetise this — be concrete, not generic",
  "signal_rating": "🟢 or 🟡 or 🔴",
  "tags": ["tag1", "tag2", "tag3"],
  "enriched_content": "Full structured note (3-5 paragraphs) with V's context woven in. Include: what it is, why it matters, specific next action, connection to V's goals."
}}

Rating guide:
- 🟢 Must-act: directly impacts V's revenue, career, or active build. Demands action within 48hrs.
- 🟡 Valuable: useful knowledge or insight. Worth saving. No urgent action required.
- 🔴 Noise: interesting but doesn't serve V's current mission. Archive and move on.

CRITICAL: Revenue angle must be SPECIFIC to V's situation (finance + AI + teaching + building). Not generic advice.
"""


# ── URL detection ─────────────────────────────────────────────────────

_URL_PATTERN = re.compile(
    r"https?://[^\s<>\"\'\)\]]+",
    re.IGNORECASE,
)


def _extract_urls(text: str) -> list[str]:
    """Pull all URLs from text."""
    return _URL_PATTERN.findall(text)


def _is_url_drop(text: str) -> bool:
    """Check if the input is primarily a URL drop (URL is >50% of content)."""
    urls = _extract_urls(text)
    if not urls:
        return False
    url_chars = sum(len(u) for u in urls)
    return url_chars > len(text.strip()) * 0.4


# ── Core orchestration ────────────────────────────────────────────────

def orchestrate(
    content: str,
    *,
    agent_override: str | None = None,
    source_url: str | None = None,
    skip_llm: bool = False,
) -> EnrichedCapture:
    """Run the full orchestration pipeline on raw input.

    1. Detect agent from content signals
    2. If URL detected → fetch + extract page content
    3. Load agent SKILL.md as system context
    4. Call Claude Haiku for structured enrichment
    5. Return EnrichedCapture ready for Obsidian + SQLite

    Args:
        content: Raw text from V (thought, URL, brain dump, statement)
        agent_override: Force a specific agent (skip detection)
        source_url: Explicit URL if known
        skip_llm: If True, skip LLM enrichment (for when API keys unavailable)

    Returns:
        EnrichedCapture with all structured fields populated
    """
    # Step 1: Detect agent
    agent = agent_override or detect_agent(content)
    log.info("Orchestrator: routing to %s", agent)

    # Step 2: URL processing
    url_context = ""
    detected_url = source_url or ""
    if not detected_url:
        urls = _extract_urls(content)
        if urls:
            detected_url = urls[0]

    if detected_url:
        url_context = _fetch_url_context(detected_url)

    # Step 3: Load agent personality
    agent_prompt = _load_agent_prompt(agent)

    # Step 4: LLM enrichment
    if skip_llm:
        return _fallback_enrichment(content, agent, detected_url)

    try:
        return _llm_enrich(
            content=content,
            agent=agent,
            agent_prompt=agent_prompt,
            url_context=url_context,
            source_url=detected_url,
        )
    except Exception as e:
        log.error("LLM enrichment failed: %s — falling back to static", e)
        return _fallback_enrichment(content, agent, detected_url)


def _llm_enrich(
    *,
    content: str,
    agent: str,
    agent_prompt: str,
    url_context: str,
    source_url: str,
) -> EnrichedCapture:
    """Call Claude Haiku with agent context to produce structured enrichment."""
    from vaishali.core.llm_client import llm

    system = f"You are {agent} from V AgentForce.\n\n{agent_prompt}" if agent_prompt else f"You are {agent} from V AgentForce."

    url_block = ""
    if url_context:
        url_block = f"URL CONTENT (fetched from {source_url}):\n{url_context[:3000]}"

    prompt = _ENRICHMENT_PROMPT.format(
        agent=agent,
        content=content,
        url_context=url_block,
    )

    response = llm.complete(
        prompt=prompt,
        system=system,
        max_tokens=1500,
        agent=f"orchestrator-{agent.lower()}",
        model="claude-haiku-4-5-20251001",
    )

    # Parse JSON response
    try:
        data = _parse_json_response(response.content)
    except Exception as e:
        log.warning("Failed to parse LLM JSON: %s", e)
        return _fallback_enrichment(content, agent, source_url)

    return EnrichedCapture(
        agent=agent,
        title=data.get("title", content[:60]),
        summary=data.get("summary", ""),
        insights=data.get("insights", []),
        revenue_angle=data.get("revenue_angle", detect_revenue_angle(agent, content)),
        signal_rating=data.get("signal_rating", "🟡"),
        tags=data.get("tags", []),
        enriched_content=data.get("enriched_content", content),
        source_url=source_url,
        url_summary=url_context[:500] if url_context else "",
        raw_input=content,
    )


def _parse_json_response(text: str) -> dict[str, Any]:
    """Parse JSON from LLM response, stripping any markdown fences."""
    clean = text.strip()
    # Remove markdown code fences if present
    if clean.startswith("```"):
        # Find the end of the opening fence
        first_newline = clean.index("\n")
        last_fence = clean.rfind("```")
        if last_fence > first_newline:
            clean = clean[first_newline + 1:last_fence].strip()
    return json.loads(clean)


def _fetch_url_context(url: str) -> str:
    """Fetch and extract readable text from a URL. Returns empty string on failure."""
    try:
        from vaishali.cipher.url_processor import fetch_and_extract
        return fetch_and_extract(url)
    except ImportError:
        log.warning("url_processor not available — skipping URL fetch")
        return ""
    except Exception as e:
        log.warning("URL fetch failed for %s: %s", url, e)
        return ""


# ── Fallback when LLM unavailable ────────────────────────────────────

def _fallback_enrichment(
    content: str,
    agent: str,
    source_url: str,
) -> EnrichedCapture:
    """Generate basic enrichment without LLM — used when API keys missing or call fails."""
    first_line = content.strip().split("\n")[0][:80]
    revenue = detect_revenue_angle(agent, content)

    return EnrichedCapture(
        agent=agent,
        title=first_line or "Untitled Capture",
        summary=content[:200],
        insights=[],
        revenue_angle=revenue,
        signal_rating="🟡",
        tags=[f"#agent/{agent.lower()}", "#capture"],
        enriched_content=content,
        source_url=source_url,
        url_summary="",
        raw_input=content,
    )
