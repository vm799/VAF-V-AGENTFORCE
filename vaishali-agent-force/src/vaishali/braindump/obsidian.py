"""Obsidian vault integration — write braindump thoughts as markdown notes.

Each thought becomes a markdown file with YAML frontmatter that Obsidian
can index, search, and display in its graph view. Thoughts also get
appended to the Obsidian daily note for that day.

The vault path is configurable via VAF_OBSIDIAN_VAULT_DIR.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from vaishali.braindump.models import Thought
from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


def _vault_dir() -> Path | None:
    """Return the Obsidian vault directory, or None if not configured."""
    vault = settings.obsidian_vault_dir
    if vault and vault.exists():
        return vault
    return None


def _sanitise_filename(text: str) -> str:
    """Make text safe for use as a filename."""
    safe = re.sub(r"[^\w\s-]", "", text).strip()
    safe = re.sub(r"\s+", "-", safe)
    return safe[:80].rstrip("-")


def write_thought_note(thought: Thought) -> Path | None:
    """Write a thought as an Obsidian markdown note with YAML frontmatter.

    Creates: {vault}/AgentForce/Braindump/{date}/{sanitised-title}.md
    Returns the path to the created note, or None if vault is not configured.
    """
    vault = _vault_dir()
    if not vault:
        log.debug("Obsidian vault not configured — skipping note creation")
        return None

    today = date.today().isoformat()
    braindump_dir = vault / "AgentForce" / "Braindump" / today
    braindump_dir.mkdir(parents=True, exist_ok=True)

    filename = _sanitise_filename(thought.title) or thought.id
    note_path = braindump_dir / f"{filename}.md"

    # Build YAML frontmatter
    frontmatter = [
        "---",
        f"id: {thought.id}",
        f"type: {thought.thought_type}",
        f"category: {thought.category}",
        f"priority: {thought.priority}",
        f"status: {thought.status}",
        f"when: \"{thought.when}\"" if thought.when else "when: \"\"",
        f"created: {thought.created_at}",
        f"tags: [{', '.join(thought.tags)}]",
        f"agents: [{', '.join(thought.linked_agents)}]",
        "---",
    ]

    # Build note body
    body = [
        f"# {thought.title}",
        "",
        thought.raw_text,
        "",
    ]

    if thought.why:
        body.extend(["## Why", "", thought.why, ""])

    if thought.when:
        body.extend(["## When", "", thought.when, ""])

    # Add agent links (Obsidian internal links)
    if thought.linked_agents:
        body.append("## Linked Agents")
        body.append("")
        for agent in thought.linked_agents:
            body.append(f"- [[AgentForce/{agent.title()}]]")
        body.append("")

    # Add tags as Obsidian tags
    if thought.tags:
        body.append("")
        body.append(" ".join(f"#{tag}" for tag in thought.tags))

    content = "\n".join(frontmatter) + "\n\n" + "\n".join(body) + "\n"
    note_path.write_text(content, encoding="utf-8")
    log.info("Wrote Obsidian note → %s", note_path.relative_to(vault))

    # Also append to daily note
    _append_to_daily_note(vault, thought)

    return note_path


def _append_to_daily_note(vault: Path, thought: Thought) -> None:
    """Append a thought reference to today's Obsidian daily note."""
    daily_dir = vault / "Daily Notes"
    daily_dir.mkdir(parents=True, exist_ok=True)

    today = date.today()
    daily_path = daily_dir / f"{today.isoformat()}.md"

    # Create daily note if it doesn't exist
    if not daily_path.exists():
        header = f"# {today.strftime('%A, %d %B %Y')}\n\n## Braindumps\n\n"
        daily_path.write_text(header, encoding="utf-8")
    else:
        existing = daily_path.read_text(encoding="utf-8")
        if "## Braindumps" not in existing:
            daily_path.write_text(existing + "\n## Braindumps\n\n", encoding="utf-8")

    # Append the thought reference
    timestamp = datetime.now().strftime("%H:%M")
    priority_emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "someday": "⚪"}.get(
        thought.priority, "🟡"
    )
    category_emoji = {
        "work": "💼", "home": "🏠", "personal": "👤", "health": "🏃",
        "finance": "💰", "learning": "📚", "creative": "🎨",
    }.get(thought.category, "💭")

    today_str = date.today().isoformat()
    note_name = _sanitise_filename(thought.title) or thought.id
    link = f"[[AgentForce/Braindump/{today_str}/{note_name}|{thought.title}]]"

    entry = f"- {timestamp} {priority_emoji} {category_emoji} {link}\n"

    with open(daily_path, "a", encoding="utf-8") as f:
        f.write(entry)

    log.debug("Appended thought to daily note → %s", daily_path.name)


def scan_vault_for_graph() -> list[dict[str, Any]]:
    """Scan the Obsidian vault's AgentForce folder for graph nodes.

    Returns a list of dicts suitable for feeding into the knowledge graph builder.
    Each dict has: id, title, type, tags, agents, date, path
    """
    vault = _vault_dir()
    if not vault:
        return []

    af_dir = vault / "AgentForce"
    if not af_dir.exists():
        return []

    items: list[dict[str, Any]] = []

    for md_file in af_dir.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")

        # Parse YAML frontmatter
        meta = _parse_frontmatter(content)
        if not meta:
            continue

        items.append({
            "id": meta.get("id", f"obs-{md_file.stem}"),
            "title": md_file.stem.replace("-", " "),
            "type": meta.get("type", "note"),
            "tags": meta.get("tags", []),
            "agents": meta.get("agents", []),
            "date": meta.get("created", ""),
            "path": str(md_file.relative_to(vault)),
            "source": "obsidian",
        })

    return items


def _parse_frontmatter(content: str) -> dict[str, Any] | None:
    """Extract YAML frontmatter from markdown content (simple parser)."""
    if not content.startswith("---"):
        return None

    end = content.find("---", 3)
    if end == -1:
        return None

    yaml_block = content[3:end].strip()
    meta: dict[str, Any] = {}

    for line in yaml_block.split("\n"):
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"')

        # Parse list values: [a, b, c]
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1]
            meta[key] = [v.strip() for v in inner.split(",") if v.strip()]
        else:
            meta[key] = value

    return meta
