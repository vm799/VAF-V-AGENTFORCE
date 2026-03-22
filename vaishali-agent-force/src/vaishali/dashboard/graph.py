"""Build a rich JSON graph of nodes and edges for the dashboard knowledge graph.

Produces Neo4j Bloom-style data with:
    - Agent hub nodes (large, central)
    - Concept / topic / entity / metric satellite nodes
    - Cross-agent relationship edges
    - Node metadata for tooltips and filtering
    - Edge weights for visual thickness
"""

from __future__ import annotations

from datetime import date
from typing import Any

from vaishali.core.logging_utils import get_logger
from vaishali.core.summaries import read_all_summaries

log = get_logger(__name__)

# Agent colours matching the design system
AGENT_META: dict[str, dict[str, str]] = {
    "finance":   {"colour": "#4ade80", "glow": "#4ade8060", "icon": "pound",  "label": "Finance"},
    "content":   {"colour": "#a78bfa", "glow": "#a78bfa60", "icon": "pen",    "label": "Content"},
    "education": {"colour": "#60a5fa", "glow": "#60a5fa60", "icon": "book",   "label": "Education"},
    "research":  {"colour": "#38bdf8", "glow": "#38bdf860", "icon": "flask",  "label": "Research"},
    "health":    {"colour": "#fb923c", "glow": "#fb923c60", "icon": "heart",  "label": "Health"},
    "braindump": {"colour": "#e879f9", "glow": "#e879f960", "icon": "brain",  "label": "Braindump"},
}

# Relationship type visual weights
EDGE_WEIGHTS: dict[str, float] = {
    "anomaly": 0.6,
    "topic": 0.8,
    "entity": 0.7,
    "idea": 0.8,
    "metric": 0.9,
    "job": 0.7,
    "inspires": 1.0,
    "correlates": 1.0,
    "recurring": 0.5,
}


def build_graph_data(day: date | None = None) -> dict[str, Any]:
    """Build the node-edge graph for the dashboard."""
    day = day or date.today()
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    node_ids: set[str] = set()

    # ── 1. Agent hub nodes ──────────────────────────────────────────
    for agent_id, meta in AGENT_META.items():
        nodes.append({
            "id": agent_id,
            "label": meta["label"],
            "type": "agent",
            "category": agent_id,
            "colour": meta["colour"],
            "glow": meta["glow"],
            "icon": meta["icon"],
            "size": 36,
            "importance": 10,
            "description": f"{meta['label']} agent — central hub",
        })
        node_ids.add(agent_id)

    # ── 2. Pull rich data from summaries ────────────────────────────
    summaries = read_all_summaries(day)

    _add_finance_nodes(summaries.get("finance"), nodes, edges, node_ids)
    _add_education_nodes(summaries.get("education"), nodes, edges, node_ids)
    _add_content_nodes(summaries.get("content"), nodes, edges, node_ids)
    _add_health_nodes(summaries.get("health"), nodes, edges, node_ids)
    _add_research_nodes(summaries.get("research"), nodes, edges, node_ids)
    _add_braindump_nodes(summaries.get("braindump"), nodes, edges, node_ids)

    # ── 3. Cross-agent relationship edges ───────────────────────────
    _add_cross_agent_edges(summaries, nodes, edges, node_ids)

    # Compute connection counts for each node
    conn_count: dict[str, int] = {}
    for e in edges:
        conn_count[e["source"]] = conn_count.get(e["source"], 0) + 1
        conn_count[e["target"]] = conn_count.get(e["target"], 0) + 1
    for n in nodes:
        n["connections"] = conn_count.get(n["id"], 0)

    # Gather all node types for filter UI
    node_types = sorted(set(n["type"] for n in nodes))

    return {
        "nodes": nodes,
        "edges": edges,
        "node_types": node_types,
        "date": day.isoformat(),
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        },
    }


# ── Finance ─────────────────────────────────────────────────────────

def _add_finance_nodes(
    fin: dict[str, Any] | None,
    nodes: list, edges: list, node_ids: set,
) -> None:
    if not fin:
        return
    colour = AGENT_META["finance"]["colour"]
    glow = AGENT_META["finance"]["glow"]

    # Recurring payments as a cluster
    recurring = fin.get("recurring_count", 0)
    if recurring > 0:
        nid = "fin:recurring"
        nodes.append({
            "id": nid, "label": f"Recurring ({recurring})", "type": "metric",
            "category": "finance", "colour": colour, "glow": glow,
            "size": 16, "importance": 6,
            "description": f"{recurring} recurring payments detected",
        })
        node_ids.add(nid)
        edges.append(_edge("finance", nid, "recurring", 0.6))

    # Anomalies
    anomalies = fin.get("anomalies", [])
    for a in anomalies[:5]:
        desc = a.get("description", "unknown")
        nid = f"fin:{desc[:20]}"
        if nid in node_ids:
            continue
        severity = a.get("severity", "low")
        imp = {"high": 8, "medium": 6, "low": 4}.get(severity, 4)
        nodes.append({
            "id": nid, "label": desc[:25], "type": "anomaly",
            "category": "finance", "colour": colour, "glow": glow,
            "size": 10 + imp, "importance": imp,
            "description": f"£{abs(a.get('amount', 0)):,.2f} — {a.get('reason', '')}",
        })
        node_ids.add(nid)
        edges.append(_edge("finance", nid, "anomaly", EDGE_WEIGHTS["anomaly"]))

    # Account balance nodes
    for acc in fin.get("accounts", [])[:3]:
        nid = f"fin:acc:{acc.get('id', '')}"
        bal = acc.get("balance", 0)
        nodes.append({
            "id": nid, "label": f"£{bal:,.0f}", "type": "metric",
            "category": "finance", "colour": colour, "glow": glow,
            "size": 20, "importance": 7,
            "description": f"{acc.get('id', 'Account')}: £{bal:,.2f} (7d: £{acc.get('net_7d', 0):+,.2f})",
        })
        node_ids.add(nid)
        edges.append(_edge("finance", nid, "balance", 0.8))


# ── Education ───────────────────────────────────────────────────────

def _add_education_nodes(
    edu: dict[str, Any] | None,
    nodes: list, edges: list, node_ids: set,
) -> None:
    if not edu:
        return
    colour = AGENT_META["education"]["colour"]
    glow = AGENT_META["education"]["glow"]

    for i, topic in enumerate(edu.get("top_topics", [])[:6]):
        nid = f"topic:{topic}"
        if nid in node_ids:
            continue
        nodes.append({
            "id": nid, "label": topic, "type": "topic",
            "category": "education", "colour": colour, "glow": glow,
            "size": 14 - i, "importance": 7 - i,
            "description": f"Learning topic: {topic}",
        })
        node_ids.add(nid)
        edges.append(_edge("education", nid, "topic", EDGE_WEIGHTS["topic"]))

    for entity in edu.get("top_entities", [])[:5]:
        nid = f"entity:{entity}"
        if nid in node_ids:
            continue
        nodes.append({
            "id": nid, "label": entity, "type": "entity",
            "category": "education", "colour": colour, "glow": glow,
            "size": 12, "importance": 5,
            "description": f"Entity: {entity}",
        })
        node_ids.add(nid)
        edges.append(_edge("education", nid, "entity", EDGE_WEIGHTS["entity"]))


# ── Content ─────────────────────────────────────────────────────────

def _add_content_nodes(
    content: dict[str, Any] | None,
    nodes: list, edges: list, node_ids: set,
) -> None:
    if not content:
        return
    colour = AGENT_META["content"]["colour"]
    glow = AGENT_META["content"]["glow"]

    for idea in content.get("top_ideas", [])[:4]:
        nid = f"idea:{idea.get('id', '')}"
        if nid in node_ids:
            continue
        nodes.append({
            "id": nid, "label": idea.get("title", "")[:28], "type": "idea",
            "category": "content", "colour": colour, "glow": glow,
            "size": 10 + idea.get("impact", 5), "importance": idea.get("impact", 5),
            "description": f"{idea.get('type', '')} · {idea.get('channel', '')} · Impact {idea.get('impact', '?')}/10",
        })
        node_ids.add(nid)
        edges.append(_edge("content", nid, "idea", EDGE_WEIGHTS["idea"]))

    for draft in content.get("drafts_waiting_review", [])[:2]:
        nid = f"draft:{draft.get('id', '')}"
        if nid in node_ids:
            continue
        nodes.append({
            "id": nid, "label": f"Review: {draft.get('title', '')[:20]}", "type": "draft",
            "category": "content", "colour": "#fbbf24",  # warning yellow
            "glow": "#fbbf2440",
            "size": 14, "importance": 7,
            "description": f"Draft waiting review: {draft.get('title', '')}",
        })
        node_ids.add(nid)
        edges.append(_edge("content", nid, "review", 0.9))


# ── Health ──────────────────────────────────────────────────────────

def _add_health_nodes(
    health: dict[str, Any] | None,
    nodes: list, edges: list, node_ids: set,
) -> None:
    if not health or health.get("body_score") is None:
        return
    colour = AGENT_META["health"]["colour"]
    glow = AGENT_META["health"]["glow"]

    metrics_map = {
        "movement": ("Steps & Workout", health.get("movement", {})),
        "sleep": ("Sleep", health.get("sleep", {})),
        "habits": ("Habits", health.get("habits", {})),
    }

    for key, (label, data) in metrics_map.items():
        if not isinstance(data, dict):
            continue
        score = data.get("score", 0)
        nid = f"health:{key}"
        detail = ""
        if key == "movement":
            detail = f"{data.get('steps', 0):,} steps · {data.get('workout_minutes', 0)}min workout"
        elif key == "sleep":
            detail = f"{data.get('hours', 0)}h sleep · HR {data.get('resting_hr', '?')}bpm"
        elif key == "habits":
            detail = f"{data.get('completed', 0)}/{data.get('total', 4)} habits · {data.get('rate', 0):.0%} rate"

        nodes.append({
            "id": nid, "label": f"{label} ({score:.0f})", "type": "metric",
            "category": "health", "colour": colour, "glow": glow,
            "size": 10 + score, "importance": score,
            "description": detail,
        })
        node_ids.add(nid)
        edges.append(_edge("health", nid, "metric", EDGE_WEIGHTS["metric"]))

    # Body score as a separate prominent node
    bs = health["body_score"]
    nid = "health:body_score"
    nodes.append({
        "id": nid, "label": f"Body {bs}/10", "type": "score",
        "category": "health", "colour": colour, "glow": glow,
        "size": 22, "importance": 9,
        "description": health.get("recommendation", ""),
    })
    node_ids.add(nid)
    edges.append(_edge("health", nid, "score", 1.0))


# ── Research ────────────────────────────────────────────────────────

def _add_research_nodes(
    research: dict[str, Any] | None,
    nodes: list, edges: list, node_ids: set,
) -> None:
    if not research:
        return
    colour = AGENT_META["research"]["colour"]
    glow = AGENT_META["research"]["glow"]

    for job in research.get("jobs_summary", [])[:4]:
        nid = f"research:{job.get('id', '')}"
        if nid in node_ids:
            continue
        priority = job.get("priority", "medium")
        imp = {"high": 8, "medium": 5, "low": 3}.get(priority, 5)
        nodes.append({
            "id": nid, "label": job.get("title", "")[:25], "type": "research_job",
            "category": "research", "colour": colour, "glow": glow,
            "size": 10 + imp, "importance": imp,
            "description": f"{job.get('status', '')} · {priority} priority · {job.get('findings_count', 0)} findings",
        })
        node_ids.add(nid)
        edges.append(_edge("research", nid, "job", EDGE_WEIGHTS["job"]))


# ── Braindump ──────────────────────────────────────────────────────

def _add_braindump_nodes(
    bd: dict[str, Any] | None,
    nodes: list, edges: list, node_ids: set,
) -> None:
    if not bd:
        return
    colour = AGENT_META["braindump"]["colour"]
    glow = AGENT_META["braindump"]["glow"]

    # Top actions as nodes
    for action in bd.get("top_actions", [])[:5]:
        nid = f"thought:{action.get('id', '')}"
        if nid in node_ids:
            continue
        priority = action.get("priority", "medium")
        imp = {"urgent": 9, "high": 7, "medium": 5, "low": 3, "someday": 2}.get(priority, 5)
        cat_emoji = {"work": "W", "home": "H", "personal": "P"}.get(action.get("category", ""), "")
        nodes.append({
            "id": nid, "label": action.get("title", "")[:28], "type": "thought",
            "category": "braindump", "colour": colour, "glow": glow,
            "size": 8 + imp, "importance": imp,
            "description": f"{priority} · {action.get('category', '')} · {action.get('when', 'no deadline')}",
        })
        node_ids.add(nid)
        edges.append(_edge("braindump", nid, "captured", 0.7))

        # Link to relevant agent if category matches
        agent_map = {"finance": "finance", "health": "health", "learning": "education", "creative": "content"}
        linked_agent = agent_map.get(action.get("category", ""))
        if linked_agent and linked_agent in node_ids:
            edges.append(_edge(nid, linked_agent, "linked_to", 0.6))

    # Category breakdown as a summary node
    by_cat = bd.get("by_category", {})
    if by_cat:
        nid = "bd:categories"
        cats = " · ".join(f"{k}: {v}" for k, v in sorted(by_cat.items(), key=lambda x: -x[1])[:4])
        nodes.append({
            "id": nid, "label": f"Thoughts ({bd.get('total_thoughts', 0)})", "type": "metric",
            "category": "braindump", "colour": colour, "glow": glow,
            "size": 18, "importance": 6,
            "description": cats,
        })
        node_ids.add(nid)
        edges.append(_edge("braindump", nid, "metric", 0.8))


# ── Cross-agent edges ───────────────────────────────────────────────

def _add_cross_agent_edges(
    summaries: dict[str, Any],
    nodes: list, edges: list, node_ids: set,
) -> None:
    edu = summaries.get("education")
    content = summaries.get("content")
    health = summaries.get("health")
    fin = summaries.get("finance")

    # Education topics → Content ideas (shared keywords)
    if edu and content:
        edu_topics = set(edu.get("top_topics", []))
        for idea in content.get("top_ideas", []):
            idea_nid = f"idea:{idea.get('id', '')}"
            if idea_nid not in node_ids:
                continue
            idea_words = set(idea.get("title", "").lower().split())
            for topic in edu_topics & idea_words:
                topic_nid = f"topic:{topic}"
                if topic_nid in node_ids:
                    edges.append(_edge(topic_nid, idea_nid, "inspires", 1.0))

    # Health mood → Finance (emotional spending correlation)
    if health and fin:
        mood = health.get("mood_energy", {})
        if isinstance(mood, dict) and mood.get("mood", 3) <= 2:
            anomalies = fin.get("anomalies", [])
            if anomalies:
                edges.append(_edge("health", "finance", "correlates", 1.0))

    # Inter-agent connections (always show the network fabric)
    edges.append(_edge("education", "research", "feeds", 0.3))
    edges.append(_edge("education", "content", "inspires", 0.3))
    edges.append(_edge("health", "content", "context", 0.2))

    # Braindump connects to all agents (it's the universal inbox)
    bd = summaries.get("braindump")
    if bd and bd.get("total_thoughts", 0) > 0:
        for agent in ["finance", "content", "education", "health"]:
            cat_map = {"finance": "finance", "creative": "content", "learning": "education", "health": "health"}
            agent_cats = [c for c, a in cat_map.items() if a == agent]
            by_cat = bd.get("by_category", {})
            if any(by_cat.get(c, 0) > 0 for c in agent_cats):
                edges.append(_edge("braindump", agent, "feeds", 0.5))


def _edge(source: str, target: str, relation: str, weight: float = 0.5) -> dict[str, Any]:
    return {
        "id": f"{source}->{target}",
        "source": source,
        "target": target,
        "relation": relation,
        "weight": weight,
    }
