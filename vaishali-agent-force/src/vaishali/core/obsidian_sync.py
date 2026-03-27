"""Obsidian vault sync — write agent summaries as daily notes with YAML frontmatter.

This module creates a daily Obsidian note per agent so the full Agent Force
state is browsable in Obsidian's graph view and search.

Vault structure:
    {vault}/AgentForce/
        Finance/
            2026-03-21.md       ← daily finance summary
        Content/
            2026-03-21.md
        Education/
            2026-03-21.md
        Health/
            2026-03-21.md
        Braindump/
            2026-03-21/
                thought-title.md ← individual braindump notes (handled by braindump/obsidian.py)
        Daily Notes/
            2026-03-21.md       ← unified daily briefing
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger
from vaishali.core.summaries import read_all_summaries

log = get_logger(__name__)


def _vault_dir() -> Path | None:
    vault = settings.obsidian_vault_dir
    if vault and vault.exists():
        return vault
    return None


def sync_all_to_obsidian(day: date | None = None) -> int:
    """Write all agent summaries to the Obsidian vault as markdown notes.

    Returns the number of notes written.
    """
    vault = _vault_dir()
    if not vault:
        log.debug("Obsidian vault not configured — skipping sync")
        return 0

    day = day or date.today()
    summaries = read_all_summaries(day)
    written = 0

    for agent, data in summaries.items():
        if not data or agent == "braindump":  # braindump has its own obsidian handler
            continue
        path = _write_agent_note(vault, agent, data, day)
        if path:
            written += 1

    # Write unified daily briefing
    briefing_path = settings.briefings_dir / f"{day.isoformat()}.json"
    if briefing_path.exists():
        briefing = json.loads(briefing_path.read_text(encoding="utf-8"))
        path = _write_daily_briefing(vault, briefing, day)
        if path:
            written += 1

    log.info("Synced %d notes to Obsidian vault", written)
    return written


def _write_agent_note(vault: Path, agent: str, data: dict[str, Any], day: date) -> Path | None:
    """Write a single agent's daily summary as an Obsidian note."""
    agent_dir = vault / "AgentForce" / agent.title()
    agent_dir.mkdir(parents=True, exist_ok=True)

    note_path = agent_dir / f"{day.isoformat()}.md"

    # Build YAML frontmatter
    status = data.get("status", "idle")
    mood = data.get("mood", "")
    headline = data.get("headline", "")

    frontmatter = [
        "---",
        f"agent: {agent}",
        f"date: {day.isoformat()}",
        f"status: {status}",
        f"mood: \"{mood}\"",
        "type: agent-summary",
        "---",
    ]

    # Agent-specific body
    body = [
        f"# {_agent_emoji(agent)} {agent.title()} — {day.strftime('%A %d %B %Y')}",
        "",
        f"**Status:** {status} | **Mood:** {mood}",
        "",
        f"> {headline}" if headline else "",
        "",
    ]

    if agent == "finance":
        body.extend(_format_finance(data))
    elif agent == "content":
        body.extend(_format_content(data))
    elif agent == "education":
        body.extend(_format_education(data))
    elif agent == "health":
        body.extend(_format_health(data))
    elif agent == "research":
        body.extend(_format_research(data))

    content = "\n".join(frontmatter) + "\n\n" + "\n".join(body) + "\n"
    note_path.write_text(content, encoding="utf-8")
    return note_path


def _write_daily_briefing(vault: Path, briefing: dict[str, Any], day: date) -> Path | None:
    """Write the unified daily briefing to Obsidian."""
    daily_dir = vault / "AgentForce" / "Briefings"
    daily_dir.mkdir(parents=True, exist_ok=True)

    note_path = daily_dir / f"{day.isoformat()}.md"

    frontmatter = [
        "---",
        f"date: {day.isoformat()}",
        "type: daily-briefing",
        "---",
    ]

    body = [
        f"# Daily Briefing — {day.strftime('%A %d %B %Y')}",
        "",
    ]

    wm = briefing.get("what_matters_most_today", "")
    if wm:
        body.extend(["## What Matters Most", "", wm, ""])

    win = briefing.get("todays_win", "")
    if win:
        body.extend(["## Today's Win", "", win, ""])

    headlines = briefing.get("agent_headlines", {})
    if headlines:
        body.append("## Agent Status")
        body.append("")
        for agent, headline in headlines.items():
            emoji = _agent_emoji(agent)
            body.append(f"- {emoji} **{agent.title()}:** {headline}")
        body.append("")

    insights = briefing.get("cross_agent_insights", [])
    if insights:
        body.append("## Cross-Agent Insights")
        body.append("")
        for i in insights[:5]:
            body.append(f"- {i}")
        body.append("")

    # Link to individual agent notes
    body.extend([
        "## Agent Notes",
        "",
        f"- [[AgentForce/Finance/{day.isoformat()}|Finance]]",
        f"- [[AgentForce/Content/{day.isoformat()}|Content]]",
        f"- [[AgentForce/Education/{day.isoformat()}|Education]]",
        f"- [[AgentForce/Health/{day.isoformat()}|Health]]",
    ])

    content = "\n".join(frontmatter) + "\n\n" + "\n".join(body) + "\n"
    note_path.write_text(content, encoding="utf-8")
    return note_path


# ── Agent-specific formatters ──────────────────────────────────────────

def _format_finance(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    total = data.get("total_balance_gbp")
    if total is not None:
        lines.extend(["## Balance", "", f"**Total:** £{total:,.2f}", ""])

    accounts = data.get("accounts", [])
    if accounts:
        lines.append("## Accounts")
        lines.append("")
        for acc in accounts:
            net_7d = acc.get("net_7d", 0)
            direction = "+" if net_7d >= 0 else ""
            lines.append(f"- **{acc.get('id', 'Account')}:** £{acc.get('balance', 0):,.2f} ({direction}£{net_7d:,.2f} 7d)")
        lines.append("")

    anomalies = data.get("anomalies", [])
    if anomalies:
        lines.append("## Anomalies")
        lines.append("")
        for a in anomalies[:5]:
            lines.append(f"- {a.get('description', '')} — £{abs(a.get('amount', 0)):,.2f} ({a.get('severity', 'low')})")
        lines.append("")

    return lines


def _format_content(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    lines.extend([f"**Backlog:** {data.get('total_backlog', 0)} items", ""])

    top = data.get("top_ideas", [])
    if top:
        lines.append("## Top Ideas")
        lines.append("")
        for idea in top[:5]:
            lines.append(f"- **{idea.get('title', '')}** ({idea.get('type', '')} · {idea.get('channel', '')} · Impact {idea.get('impact', '?')}/10)")
        lines.append("")

    waiting = data.get("drafts_waiting_review", [])
    if waiting:
        lines.append("## Drafts Needing Review")
        lines.append("")
        for d in waiting:
            lines.append(f"- {d.get('title', '')}")
        lines.append("")

    return lines


def _format_education(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    items = data.get("items_processed", 0)
    lines.extend([f"**Items processed:** {items}", ""])

    topics = data.get("top_topics", [])
    if topics:
        lines.append(f"**Topics:** {', '.join(topics[:6])}")
        lines.append("")

    insights = data.get("new_insights", [])
    if insights:
        lines.append("## Insights")
        lines.append("")
        for i in insights[:5]:
            lines.append(f"- {i}")
        lines.append("")

    return lines


def _format_health(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    score = data.get("body_score")
    if score is not None:
        lines.extend([f"## Body Score: {score}/10", ""])

    movement = data.get("movement", {})
    if isinstance(movement, dict):
        lines.append(f"- **Steps:** {movement.get('steps', 0):,}")
        lines.append(f"- **Workout:** {movement.get('workout_minutes', 0)} min")

    sleep = data.get("sleep", {})
    if isinstance(sleep, dict):
        lines.append(f"- **Sleep:** {sleep.get('hours', 0)}h")

    habits = data.get("habits", {})
    if isinstance(habits, dict):
        lines.append(f"- **Habits:** {habits.get('completed', 0)}/{habits.get('total', 4)}")

    lines.append("")

    rec = data.get("recommendation")
    if rec:
        lines.extend([f"> {rec}", ""])

    return lines


def _format_research(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    jobs = data.get("jobs_summary", [])
    if jobs:
        lines.append("## Research Jobs")
        lines.append("")
        for j in jobs[:5]:
            lines.append(f"- **{j.get('title', '')}** — {j.get('status', '')} ({j.get('priority', 'medium')})")
        lines.append("")
    return lines


def _agent_emoji(agent: str) -> str:
    return {
        "finance": "🦉",
        "content": "🦊",
        "education": "🐱",
        "research": "🐱",
        "health": "🐼",
        "braindump": "🧠",
    }.get(agent, "🤖")
