"""InsightsEngine — weekly intelligence from the golden thread.

Analyses all captures from the past 7 days and generates:
  - Top themes (most recurring topics)
  - Cross-agent connections (CIPHER article + FORGE build = opportunity)
  - Revenue opportunities surfaced
  - Must-act items pending
  - Goggins score trend

Usage:
    from vaishali.insights.engine import generate_weekly_brief, get_weekly_insights

    # For Telegram /weekly command
    brief = generate_weekly_brief()

    # For dashboard InsightsPanel v2
    data = get_weekly_insights()
"""

from __future__ import annotations

import html
import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


def _captures_db() -> Path:
    return settings.data_dir / "captures.db"


def _checkins_db() -> Path:
    return settings.data_dir / "checkins.db"


def _get_recent_captures(days: int = 7) -> list[dict[str, Any]]:
    """Fetch captures from the last N days."""
    db = _captures_db()
    if not db.exists():
        return []

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM captures WHERE created_at >= ? ORDER BY id DESC",
            (cutoff,),
        ).fetchall()
    return [dict(r) for r in rows]


def _get_recent_checkins(days: int = 7) -> list[dict[str, Any]]:
    """Fetch Goggins checkins from the last N days."""
    db = _checkins_db()
    if not db.exists():
        return []

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        with sqlite3.connect(db) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM checkins WHERE checkin_date >= ? ORDER BY checkin_date DESC",
                (cutoff,),
            ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        return []


def get_weekly_insights(days: int = 7) -> dict[str, Any]:
    """Generate structured weekly insights data for the dashboard.

    Returns:
        {
            "period": "2026-03-15 to 2026-03-22",
            "total_captures": 42,
            "enriched_count": 38,
            "must_act": [...],
            "by_agent": {"CIPHER": 12, "FORGE": 8, ...},
            "top_themes": [{"theme": "LangGraph", "count": 5, "agents": ["FORGE", "CIPHER"]}, ...],
            "revenue_opportunities": [...],
            "cross_agent_connections": [...],
            "goggins": {"avg_score": 35.2, "best_day": "2026-03-20", "streak": 5},
            "content_ideas": [...],
        }
    """
    captures = _get_recent_captures(days)
    checkins = _get_recent_checkins(days)

    now = datetime.now()
    start = now - timedelta(days=days)

    # Agent distribution
    agent_counts: Counter = Counter(c.get("agent", "UNKNOWN") for c in captures)

    # Must-act items
    must_act = [c for c in captures if c.get("signal_rating") == "🟢"]

    # Enriched count
    enriched_count = sum(1 for c in captures if c.get("enriched"))

    # Extract themes from tags and titles
    themes = _extract_themes(captures)

    # Revenue opportunities
    revenue_ops = _extract_revenue_opportunities(captures)

    # Cross-agent connections
    connections = _find_cross_agent_connections(captures)

    # Content ideas from captures
    content_ideas = _generate_content_ideas(captures)

    # Goggins stats
    goggins = _goggins_stats(checkins)

    return {
        "period": f"{start.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
        "total_captures": len(captures),
        "enriched_count": enriched_count,
        "must_act": [_capture_summary(c) for c in must_act[:5]],
        "by_agent": dict(agent_counts.most_common()),
        "top_themes": themes[:8],
        "revenue_opportunities": revenue_ops[:5],
        "cross_agent_connections": connections[:5],
        "goggins": goggins,
        "content_ideas": content_ideas[:5],
    }


def _extract_themes(captures: list[dict]) -> list[dict[str, Any]]:
    """Extract recurring themes from capture tags and titles."""
    word_agents: dict[str, set[str]] = {}
    word_counts: Counter = Counter()

    # Stop words to ignore
    stops = {
        "the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to",
        "for", "of", "and", "or", "but", "not", "with", "this", "that", "from",
        "it", "its", "my", "your", "our", "we", "can", "how", "what", "will",
        "just", "about", "been", "have", "has", "had", "more", "than", "new",
        "all", "also", "any", "some",
    }

    for cap in captures:
        agent = cap.get("agent", "UNKNOWN")

        # Extract words from title
        title = cap.get("title", "")
        words = [w.lower().strip(".,!?;:()[]{}\"'") for w in title.split() if len(w) > 3]
        words = [w for w in words if w not in stops and w.isalpha()]

        # Extract from tags
        try:
            tags = json.loads(cap.get("tags", "[]"))
            for tag in tags:
                clean = tag.replace("#", "").replace("agent/", "").replace("vaf", "").strip()
                if clean and len(clean) > 3:
                    words.append(clean.lower())
        except (json.JSONDecodeError, TypeError):
            pass

        for w in words:
            word_counts[w] += 1
            if w not in word_agents:
                word_agents[w] = set()
            word_agents[w].add(agent)

    # Only keep themes that appear 2+ times
    themes = []
    for word, count in word_counts.most_common(20):
        if count >= 2:
            themes.append({
                "theme": word,
                "count": count,
                "agents": sorted(word_agents.get(word, set())),
            })

    return themes


def _extract_revenue_opportunities(captures: list[dict]) -> list[dict[str, Any]]:
    """Pull revenue angles from captures."""
    ops = []
    for cap in captures:
        angle = cap.get("revenue_angle", "")
        if angle and "💰" in angle:
            ops.append({
                "agent": cap.get("agent", "UNKNOWN"),
                "title": cap.get("title", "")[:60],
                "angle": angle,
                "signal": cap.get("signal_rating", "🟡"),
            })
    # Prioritise 🟢 must-act
    ops.sort(key=lambda x: (x["signal"] != "🟢", x["signal"] != "🟡"))
    return ops


def _find_cross_agent_connections(captures: list[dict]) -> list[dict[str, Any]]:
    """Find topics that appear across multiple agents — these are opportunities."""
    # Group captures by extracted theme words
    theme_captures: dict[str, list[dict]] = {}

    for cap in captures:
        title_words = {w.lower() for w in cap.get("title", "").split() if len(w) > 4}
        for word in title_words:
            if word not in theme_captures:
                theme_captures[word] = []
            theme_captures[word].append(cap)

    connections = []
    for word, caps in theme_captures.items():
        agents = {c.get("agent") for c in caps}
        if len(agents) >= 2:
            connections.append({
                "topic": word,
                "agents": sorted(agents),
                "capture_count": len(caps),
                "insight": f"{' + '.join(sorted(agents))} both flagged '{word}' — potential cross-domain opportunity",
            })

    connections.sort(key=lambda x: -x["capture_count"])
    return connections


def _generate_content_ideas(captures: list[dict]) -> list[dict[str, Any]]:
    """Generate AMPLIFY content ideas from this week's captures."""
    ideas = []
    for cap in captures:
        agent = cap.get("agent", "")
        title = cap.get("title", "")
        if not title:
            continue

        # Every capture is a potential content piece
        if agent == "FORGE":
            ideas.append({
                "hook": f"I built {title[:50]} — here's what I learned",
                "platform": "LinkedIn",
                "from_agent": agent,
            })
        elif agent == "CIPHER":
            ideas.append({
                "hook": f"The most important thing I learned about {title[:40]} this week",
                "platform": "LinkedIn / Twitter",
                "from_agent": agent,
            })
        elif agent == "PHOENIX":
            ideas.append({
                "hook": f"What {title[:40]} taught me about AI + finance",
                "platform": "Substack",
                "from_agent": agent,
            })
        elif agent == "AEGIS":
            ideas.append({
                "hook": f"AI security insight: {title[:40]}",
                "platform": "LinkedIn",
                "from_agent": agent,
            })

    return ideas


def _goggins_stats(checkins: list[dict]) -> dict[str, Any]:
    """Compute Goggins protocol stats for the period."""
    if not checkins:
        return {"avg_score": 0, "best_day": "N/A", "days_checked": 0, "streak": 0}

    pillars = ["body", "build", "learn", "amplify", "brief"]
    totals = []
    best_score = 0
    best_day = ""

    for ci in checkins:
        total = sum(ci.get(p, 0) for p in pillars)
        totals.append(total)
        if total > best_score:
            best_score = total
            best_day = ci.get("checkin_date", "")

    # Streak: consecutive days >= 25
    streak = 0
    for t in totals:
        if t >= 25:
            streak += 1
        else:
            break

    return {
        "avg_score": round(sum(totals) / len(totals), 1) if totals else 0,
        "best_day": best_day,
        "best_score": best_score,
        "days_checked": len(checkins),
        "streak": streak,
    }


def _capture_summary(cap: dict) -> dict[str, Any]:
    """Minimal capture summary for display."""
    return {
        "agent": cap.get("agent", "UNKNOWN"),
        "title": cap.get("title", "")[:80],
        "signal": cap.get("signal_rating", "🟡"),
        "created_at": cap.get("created_at", "")[:10],
        "revenue_angle": cap.get("revenue_angle", ""),
    }


# ── Telegram-formatted weekly brief ──────────────────────────────────

def generate_weekly_brief(days: int = 7) -> str:
    """Generate HTML-formatted weekly brief for Telegram /weekly command."""
    data = get_weekly_insights(days)
    _e = html.escape

    lines = [
        f"📊 <b>WEEKLY INTELLIGENCE BRIEF</b>",
        f"<i>{_e(data['period'])}</i>\n",
    ]

    # Stats
    lines.append(
        f"📎 <b>{data['total_captures']}</b> captures "
        f"({data['enriched_count']} enriched) · "
        f"{len(data['must_act'])} 🟢 must-act"
    )

    # Agent breakdown
    if data["by_agent"]:
        agent_str = " · ".join(f"{a}: {c}" for a, c in data["by_agent"].items())
        lines.append(f"\n🎖️ <b>By Agent:</b> {_e(agent_str)}")

    # Must-act items
    if data["must_act"]:
        lines.append("\n🟢 <b>MUST-ACT THIS WEEK:</b>")
        for item in data["must_act"]:
            lines.append(f"  • <b>{_e(item['agent'])}</b>: {_e(item['title'])}")

    # Top themes
    if data["top_themes"]:
        lines.append("\n🔥 <b>TOP THEMES:</b>")
        for t in data["top_themes"][:5]:
            agents = ", ".join(t["agents"])
            lines.append(f"  • <b>{_e(t['theme'])}</b> ({t['count']}×) — {_e(agents)}")

    # Cross-agent connections
    if data["cross_agent_connections"]:
        lines.append("\n🔗 <b>CROSS-AGENT CONNECTIONS:</b>")
        for conn in data["cross_agent_connections"][:3]:
            lines.append(f"  • {_e(conn['insight'])}")

    # Content ideas
    if data["content_ideas"]:
        lines.append("\n📱 <b>CONTENT IDEAS (AMPLIFY):</b>")
        for idea in data["content_ideas"][:3]:
            lines.append(f"  • {_e(idea['hook'])} → {_e(idea['platform'])}")

    # Goggins
    g = data["goggins"]
    if g["days_checked"] > 0:
        lines.append(
            f"\n🔥 <b>GOGGINS:</b> avg {g['avg_score']}/50 · "
            f"best {g['best_score']}/50 ({_e(g['best_day'])}) · "
            f"streak {g['streak']}d"
        )

    lines.append("\n<i>Stay hard. Stay building. The empire doesn't build itself.</i>")

    return "\n".join(lines)
