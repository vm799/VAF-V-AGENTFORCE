"""Insight Engine — compose all agent summaries into a unified daily briefing.

Produces:
    - what_matters_most_today (one bold line)
    - todays_win (one celebratory line)
    - cross_agent_insights (2–5 bullets)
    - Unified briefing JSON + Markdown
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


def generate_briefing(day: date | None = None) -> dict[str, Any]:
    """Load all agent summaries and produce a unified briefing."""
    day = day or date.today()
    summaries = read_all_summaries(day)

    what_matters = _what_matters_most(summaries, day)
    win = _todays_win(summaries)
    insights = _cross_agent_insights(summaries)

    briefing: dict[str, Any] = {
        "date": day.isoformat(),
        "what_matters_most_today": what_matters,
        "todays_win": win,
        "cross_agent_insights": insights,
        "agent_headlines": {
            agent: (s.get("headline", "No data") if s else "No data")
            for agent, s in summaries.items()
        },
        "summaries": {
            agent: s for agent, s in summaries.items() if s
        },
    }

    # Write JSON
    json_path = settings.briefings_dir / f"{day.isoformat()}.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(briefing, indent=2, default=str), encoding="utf-8")
    log.info("Briefing JSON → %s", json_path.name)

    # Write Markdown
    md_path = settings.reports_dir / "daily" / f"{day.isoformat()}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_render_markdown(briefing, day), encoding="utf-8")
    log.info("Briefing Markdown → %s", md_path.name)

    return briefing


def _what_matters_most(summaries: dict[str, Any], day: date) -> str:
    """Determine the single most important thing today."""
    priorities: list[tuple[int, str]] = []

    # Finance: flag if anomalies or big negative change
    fin = summaries.get("finance")
    if fin:
        anomalies = fin.get("anomalies", [])
        if len(anomalies) > 3:
            priorities.append((8, f"Review {len(anomalies)} financial anomalies flagged today."))
        total_bal = fin.get("total_balance_gbp", 0)
        accounts = fin.get("accounts", [])
        if accounts:
            net_7d = sum(a.get("net_7d", 0) for a in accounts)
            if net_7d < -500:
                priorities.append((9, f"Spending alert: £{abs(net_7d):,.0f} net outflow in 7 days."))

    # Health: flag if body score is low
    health = summaries.get("health")
    if health and health.get("body_score") is not None:
        bs = health["body_score"]
        if bs < 5:
            priorities.append((7, f"Health needs attention — body score {bs}/10. {health.get('recommendation', '')}"))

    # Content: flag if drafts waiting
    content = summaries.get("content")
    if content:
        waiting = content.get("drafts_waiting_review", [])
        if waiting:
            priorities.append((5, f"{len(waiting)} content drafts waiting for your review."))

    # Research: flag active high-priority jobs
    research = summaries.get("research")
    if research:
        jobs = research.get("jobs_summary", [])
        high = [j for j in jobs if j.get("priority") == "high"]
        if high:
            priorities.append((6, f"High-priority research: {high[0].get('title', 'Untitled')}"))

    # Education: insights available
    edu = summaries.get("education")
    if edu and edu.get("items_processed", 0) > 0:
        priorities.append((3, f"{edu['items_processed']} new learning items to review."))

    if not priorities:
        return f"A fresh day awaits — {day.strftime('%A %d %B %Y')}."

    priorities.sort(key=lambda p: p[0], reverse=True)
    return priorities[0][1]


def _todays_win(summaries: dict[str, Any]) -> str:
    """Find something positive to celebrate."""
    wins: list[str] = []

    health = summaries.get("health")
    if health:
        streaks = health.get("streaks", {})
        walk = streaks.get("walk_streak", 0)
        workout = streaks.get("workout_streak", 0)
        if walk >= 3:
            wins.append(f"{walk}-day walking streak — keep it going!")
        if workout >= 3:
            wins.append(f"{workout}-day workout streak!")
        if health.get("body_score", 0) and health["body_score"] >= 8:
            wins.append(f"Excellent body score: {health['body_score']}/10!")

    content = summaries.get("content")
    if content and content.get("total_backlog", 0) > 10:
        wins.append(f"Content pipeline strong: {content['total_backlog']} ideas in the backlog.")

    edu = summaries.get("education")
    if edu and edu.get("items_processed", 0) >= 5:
        wins.append(f"Knowledge expanding: {edu['items_processed']} items learned today.")

    fin = summaries.get("finance")
    if fin:
        accounts = fin.get("accounts", [])
        for a in accounts:
            if a.get("net_30d", 0) > 0:
                wins.append(f"Positive 30-day cash flow: +£{a['net_30d']:,.0f}.")
                break

    return wins[0] if wins else "Every step forward counts. You're building something great."


def _cross_agent_insights(summaries: dict[str, Any]) -> list[str]:
    """Generate 2–5 cross-agent insights."""
    insights: list[str] = []

    health = summaries.get("health")
    fin = summaries.get("finance")

    # Health × Finance: low mood + spending
    if health and fin:
        mood = health.get("mood_energy", {}).get("mood", 3)
        anomalies = fin.get("anomalies", [])
        if mood <= 2 and anomalies:
            insights.append("Low mood correlates with spending anomalies — consider an emotional spending check.")

    # Education × Content: learning feeds content
    edu = summaries.get("education")
    content = summaries.get("content")
    if edu and content:
        edu_topics = edu.get("top_topics", [])
        if edu_topics:
            insights.append(f"Today's learning ({', '.join(edu_topics[:3])}) could fuel new content ideas.")

    # Health × Content: streak content
    if health:
        streaks = health.get("streaks", {})
        if streaks.get("walk_streak", 0) >= 7:
            insights.append("7+ day walking streak — perfect content for a LinkedIn post about consistency!")

    # Finance overview
    if fin:
        total = fin.get("total_balance_gbp", 0)
        if total > 0:
            insights.append(f"Financial position: £{total:,.0f} total balance across all accounts.")

    # Research × Education
    research = summaries.get("research")
    if research and research.get("active_jobs", 0) > 0:
        insights.append(f"{research['active_jobs']} active research jobs — check for overlap with today's learning.")

    return insights[:5]


def _render_markdown(briefing: dict[str, Any], day: date) -> str:
    """Render the briefing as a Markdown daily note."""
    lines = [
        f"# Vaishali Daily Briefing — {day.strftime('%A %d %B %Y')}",
        "",
        f"## What Matters Most Today",
        "",
        f"> {briefing['what_matters_most_today']}",
        "",
        f"## Today's Win",
        "",
        f"> {briefing['todays_win']}",
        "",
    ]

    insights = briefing.get("cross_agent_insights", [])
    if insights:
        lines.extend(["## Cross-Agent Insights", ""])
        for insight in insights:
            lines.append(f"- {insight}")
        lines.append("")

    lines.extend(["## Agent Headlines", ""])
    for agent, headline in briefing.get("agent_headlines", {}).items():
        icon = {"finance": "💰", "content": "✍️", "education": "📚", "research": "🔬", "health": "💪"}.get(agent, "📊")
        lines.append(f"- {icon} **{agent.title()}**: {headline}")

    lines.extend(["", "---", f"_Generated {day.isoformat()}_"])
    return "\n".join(lines)
