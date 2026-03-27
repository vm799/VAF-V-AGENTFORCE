"""Voice briefing — render a spoken script from today's briefing and use macOS TTS."""

from __future__ import annotations

import json
import subprocess
from datetime import date
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


def speak_briefing(text: str) -> None:
    """Speak the given text aloud using macOS `say` command.

    Falls back to logging if `say` is not available (e.g., Linux).
    """
    try:
        subprocess.Popen(
            ["say", "-v", "Samantha", "-r", "175", text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log.info("Speaking briefing via macOS TTS (%d chars)", len(text))
    except FileNotFoundError:
        log.warning("macOS `say` not available — printing briefing text instead")
        print(text)


def render_briefing_script(briefing: dict[str, Any]) -> str:
    """Render a briefing JSON into a ~5 minute spoken script."""
    day = briefing.get("date", date.today().isoformat())
    lines: list[str] = []

    lines.append(f"Good morning Vaishali. Here's your briefing for {_format_date(day)}.")
    lines.append("")

    # What matters most
    wm = briefing.get("what_matters_most_today", "")
    if wm:
        lines.append(f"What matters most today: {wm}")
        lines.append("")

    # Today's win
    win = briefing.get("todays_win", "")
    if win:
        lines.append(f"Today's win: {win}")
        lines.append("")

    # Agent headlines
    headlines = briefing.get("agent_headlines", {})
    if headlines:
        lines.append("Here's a quick look at each area:")
        lines.append("")

        for agent, headline in headlines.items():
            label = agent.replace("_", " ").title()
            lines.append(f"{label}: {headline}")
            lines.append("")

    # Cross-agent insights
    insights = briefing.get("cross_agent_insights", [])
    if insights:
        lines.append("A few cross-cutting insights:")
        for insight in insights:
            lines.append(f"  {insight}")
        lines.append("")

    # Health detail if available
    health = briefing.get("summaries", {}).get("health")
    if health and health.get("body_score") is not None:
        lines.append(f"Body score: {health['body_score']} out of 10.")
        comments = health.get("comments", [])
        for c in comments[:3]:
            lines.append(f"  {c}")
        rec = health.get("recommendation", "")
        if rec:
            lines.append(f"Recommendation: {rec}")
        lines.append("")

    # Finance detail if available
    finance = briefing.get("summaries", {}).get("finance")
    if finance:
        total = finance.get("total_balance_gbp", 0)
        lines.append(f"Total balance across accounts: £{total:,.0f}.")
        accounts = finance.get("accounts", [])
        for a in accounts[:3]:
            lines.append(f"  {a.get('id', 'Account')}: £{a.get('balance', 0):,.0f}, "
                         f"seven day change £{a.get('net_7d', 0):+,.0f}.")
        lines.append("")

    lines.append("That's your briefing. Have a great day Vaishali.")
    return "\n".join(lines)


def speak_briefing_for_today() -> dict[str, Any]:
    """Load today's briefing JSON and speak it."""
    today = date.today()
    path = settings.briefings_dir / f"{today.isoformat()}.json"

    if not path.exists():
        raise FileNotFoundError(f"No briefing found for {today}. Run morning briefing first.")

    briefing = json.loads(path.read_text(encoding="utf-8"))
    script = render_briefing_script(briefing)

    # Estimate duration: ~150 words/minute
    word_count = len(script.split())
    duration_minutes = round(word_count / 150, 1)

    speak_briefing(script)

    return {
        "script": script,
        "word_count": word_count,
        "duration_estimate": f"~{duration_minutes} minutes",
    }


def _format_date(iso_date: str) -> str:
    """Format ISO date string to spoken form."""
    try:
        d = date.fromisoformat(iso_date)
        return d.strftime("%A %d %B %Y")
    except (ValueError, TypeError):
        return iso_date
