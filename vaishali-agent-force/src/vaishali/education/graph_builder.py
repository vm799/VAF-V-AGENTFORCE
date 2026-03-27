"""Build and maintain a lightweight knowledge graph in data/education/index.json.

The graph tracks items (content), topics, entities, and links between them.
Designed to be consumed by the dashboard's KnowledgeGraph component.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


@dataclass
class GraphNode:
    id: str
    label: str
    type: str  # "item", "topic", "entity", "agent"
    weight: int = 1  # Higher = more connections/mentions
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str  # "mentions", "tagged", "related_to"
    weight: int = 1


@dataclass
class KnowledgeGraph:
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    last_updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [asdict(n) for n in self.nodes],
            "edges": [asdict(e) for e in self.edges],
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeGraph:
        return cls(
            nodes=[GraphNode(**n) for n in data.get("nodes", [])],
            edges=[GraphEdge(**e) for e in data.get("edges", [])],
            last_updated=data.get("last_updated", ""),
        )


def load_graph() -> KnowledgeGraph:
    """Load the knowledge graph from disk, or return empty if not found."""
    path = settings.education_index_path
    if not path.exists():
        return KnowledgeGraph()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return KnowledgeGraph.from_dict(data)
    except (json.JSONDecodeError, KeyError) as e:
        log.warning("Failed to load graph: %s — starting fresh", e)
        return KnowledgeGraph()


def save_graph(graph: KnowledgeGraph) -> Path:
    """Save the knowledge graph to disk."""
    path = settings.education_index_path
    path.parent.mkdir(parents=True, exist_ok=True)
    graph.last_updated = date.today().isoformat()
    path.write_text(json.dumps(graph.to_dict(), indent=2), encoding="utf-8")
    log.info("Saved knowledge graph → %s (%d nodes, %d edges)", path.name, len(graph.nodes), len(graph.edges))
    return path


def update_graph(
    graph: KnowledgeGraph,
    items: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
) -> KnowledgeGraph:
    """Update the graph with new items and their extracted topics/entities.

    Args:
        graph: Existing graph to update in place.
        items: Raw source items (from ingestion).
        summaries: Content summaries with key_entities and key_topics.
    """
    existing_node_ids = {n.id for n in graph.nodes}
    existing_edges = {(e.source, e.target, e.relation) for e in graph.edges}

    for item, summary in zip(items, summaries):
        item_id = item.get("id", "")
        if not item_id:
            continue

        # Add item node
        if item_id not in existing_node_ids:
            graph.nodes.append(
                GraphNode(
                    id=item_id,
                    label=item.get("title", "Untitled")[:60],
                    type="item",
                    metadata={
                        "url": item.get("url", ""),
                        "source": item.get("source_name", ""),
                        "date": item.get("fetched_at", ""),
                    },
                )
            )
            existing_node_ids.add(item_id)

        # Add entity nodes and edges
        for entity in summary.get("key_entities", []):
            entity_id = f"entity:{entity}"
            if entity_id not in existing_node_ids:
                graph.nodes.append(GraphNode(id=entity_id, label=entity, type="entity"))
                existing_node_ids.add(entity_id)
            else:
                # Increment weight
                for n in graph.nodes:
                    if n.id == entity_id:
                        n.weight += 1
                        break

            edge_key = (item_id, entity_id, "mentions")
            if edge_key not in existing_edges:
                graph.edges.append(GraphEdge(source=item_id, target=entity_id, relation="mentions"))
                existing_edges.add(edge_key)

        # Add topic nodes and edges
        for topic in summary.get("key_topics", [])[:5]:
            topic_id = f"topic:{topic}"
            if topic_id not in existing_node_ids:
                graph.nodes.append(GraphNode(id=topic_id, label=topic, type="topic"))
                existing_node_ids.add(topic_id)
            else:
                for n in graph.nodes:
                    if n.id == topic_id:
                        n.weight += 1
                        break

            edge_key = (item_id, topic_id, "tagged")
            if edge_key not in existing_edges:
                graph.edges.append(GraphEdge(source=item_id, target=topic_id, relation="tagged"))
                existing_edges.add(edge_key)

    # Prune: keep only the 200 highest-weight nodes + their edges
    if len(graph.nodes) > 200:
        graph.nodes.sort(key=lambda n: n.weight, reverse=True)
        keep_ids = {n.id for n in graph.nodes[:200]}
        graph.nodes = graph.nodes[:200]
        graph.edges = [e for e in graph.edges if e.source in keep_ids and e.target in keep_ids]

    return graph


def ingest_braindump_thoughts(graph: KnowledgeGraph) -> KnowledgeGraph:
    """Add braindump thoughts to the knowledge graph.

    Each thought becomes a node typed 'thought', linked to its category,
    tags, and any connected agents.
    """
    try:
        from vaishali.braindump.storage import load_thoughts
    except ImportError:
        log.warning("braindump module not available — skipping graph ingest")
        return graph

    thoughts = load_thoughts()
    if not thoughts:
        return graph

    existing_ids = {n.id for n in graph.nodes}
    existing_edges = {(e.source, e.target, e.relation) for e in graph.edges}

    for t in thoughts:
        if t.id in existing_ids:
            continue

        # Add the thought as a node
        graph.nodes.append(
            GraphNode(
                id=t.id,
                label=t.title[:60],
                type="thought",
                weight={"urgent": 5, "high": 4, "medium": 3, "low": 2, "someday": 1}.get(t.priority, 3),
                metadata={
                    "thought_type": t.thought_type,
                    "category": t.category,
                    "priority": t.priority,
                    "when": t.when,
                    "created": t.created_at,
                },
            )
        )
        existing_ids.add(t.id)

        # Link to category node
        cat_id = f"category:{t.category}"
        if cat_id not in existing_ids:
            graph.nodes.append(GraphNode(id=cat_id, label=t.category.title(), type="category", weight=1))
            existing_ids.add(cat_id)
        else:
            for n in graph.nodes:
                if n.id == cat_id:
                    n.weight += 1
                    break
        edge_key = (t.id, cat_id, "categorised_as")
        if edge_key not in existing_edges:
            graph.edges.append(GraphEdge(source=t.id, target=cat_id, relation="categorised_as"))
            existing_edges.add(edge_key)

        # Link to tags as topic nodes
        for tag in t.tags[:5]:
            tag_id = f"topic:{tag}"
            if tag_id not in existing_ids:
                graph.nodes.append(GraphNode(id=tag_id, label=tag, type="topic"))
                existing_ids.add(tag_id)
            else:
                for n in graph.nodes:
                    if n.id == tag_id:
                        n.weight += 1
                        break
            edge_key = (t.id, tag_id, "tagged")
            if edge_key not in existing_edges:
                graph.edges.append(GraphEdge(source=t.id, target=tag_id, relation="tagged"))
                existing_edges.add(edge_key)

        # Link to agent nodes
        for agent in t.linked_agents:
            agent_id = f"agent:{agent}"
            if agent_id not in existing_ids:
                graph.nodes.append(GraphNode(id=agent_id, label=agent.title(), type="agent", weight=2))
                existing_ids.add(agent_id)
            edge_key = (t.id, agent_id, "linked_to")
            if edge_key not in existing_edges:
                graph.edges.append(GraphEdge(source=t.id, target=agent_id, relation="linked_to"))
                existing_edges.add(edge_key)

    return graph


def ingest_obsidian_vault(graph: KnowledgeGraph) -> KnowledgeGraph:
    """Scan the Obsidian vault and add discovered notes to the knowledge graph."""
    try:
        from vaishali.braindump.obsidian import scan_vault_for_graph
    except ImportError:
        return graph

    vault_items = scan_vault_for_graph()
    if not vault_items:
        return graph

    existing_ids = {n.id for n in graph.nodes}
    existing_edges = {(e.source, e.target, e.relation) for e in graph.edges}

    for item in vault_items:
        item_id = item["id"]
        if item_id in existing_ids:
            continue

        graph.nodes.append(
            GraphNode(
                id=item_id,
                label=item["title"][:60],
                type="obsidian_note",
                metadata={
                    "path": item.get("path", ""),
                    "date": item.get("date", ""),
                    "source": "obsidian",
                },
            )
        )
        existing_ids.add(item_id)

        # Link to tags
        for tag in item.get("tags", [])[:5]:
            tag_id = f"topic:{tag}"
            if tag_id not in existing_ids:
                graph.nodes.append(GraphNode(id=tag_id, label=tag, type="topic"))
                existing_ids.add(tag_id)
            else:
                for n in graph.nodes:
                    if n.id == tag_id:
                        n.weight += 1
                        break
            edge_key = (item_id, tag_id, "tagged")
            if edge_key not in existing_edges:
                graph.edges.append(GraphEdge(source=item_id, target=tag_id, relation="tagged"))
                existing_edges.add(edge_key)

        # Link to agents
        for agent in item.get("agents", []):
            agent_id = f"agent:{agent}"
            if agent_id not in existing_ids:
                graph.nodes.append(GraphNode(id=agent_id, label=agent.title(), type="agent", weight=2))
                existing_ids.add(agent_id)
            edge_key = (item_id, agent_id, "linked_to")
            if edge_key not in existing_edges:
                graph.edges.append(GraphEdge(source=item_id, target=agent_id, relation="linked_to"))
                existing_edges.add(edge_key)

    return graph
