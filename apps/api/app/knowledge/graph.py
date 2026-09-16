"""Ecological knowledge graph built from KnowledgeNode/KnowledgeEdge rows.

Built fresh from the database on each call (the demo corpus is small; this
avoids stale-cache bugs). Supports multi-hop traversal used by the retrieval
term-expansion step and the reasoning engine's relationship discovery step.

Graph connectivity is never treated as proof of causation: every traversal
result carries the ``evidence_strength``/``claim_type`` of each edge so the
caller can distinguish source-supported paths from hypotheses.
"""
from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeEdge, KnowledgeNode


@dataclass
class GraphEdgeData:
    edge_id: str
    relation_type: str
    mechanism: str | None
    evidence_strength: str
    limitations: str | None
    source_claim_id: str | None


def build_graph(db: Session) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    nodes = db.query(KnowledgeNode).all()
    for node in nodes:
        graph.add_node(node.canonical_name, id=node.id, node_type=node.node_type, description=node.description)

    node_id_to_name = {n.id: n.canonical_name for n in nodes}
    edges = db.query(KnowledgeEdge).all()
    for edge in edges:
        src = node_id_to_name.get(edge.source_node_id)
        dst = node_id_to_name.get(edge.target_node_id)
        if not src or not dst:
            continue
        graph.add_edge(
            src,
            dst,
            key=edge.id,
            relation_type=edge.relation_type,
            mechanism=edge.mechanism,
            evidence_strength=edge.evidence_strength,
            limitations=edge.limitations,
            source_claim_id=edge.source_claim_id,
        )
    return graph


def neighbors_within_hops(graph: nx.MultiDiGraph, start_nodes: list[str], hops: int = 2) -> set[str]:
    """Return all node names reachable from any start node within N hops,
    traversing edges in either direction (the graph models influence, which
    is useful to expand regardless of direction for term expansion)."""
    undirected = graph.to_undirected(as_view=True)
    found: set[str] = set()
    for start in start_nodes:
        if start not in undirected:
            continue
        lengths = nx.single_source_shortest_path_length(undirected, start, cutoff=hops)
        found.update(lengths.keys())
    return found


def find_paths(graph: nx.MultiDiGraph, source: str, target: str, max_hops: int = 4) -> list[list[dict]]:
    """Return up to a few simple directed paths from source to target, each
    represented as a list of {from, relation, to, evidence_strength,
    limitations, source_claim_id} edge dicts."""
    if source not in graph or target not in graph:
        return []
    paths: list[list[dict]] = []
    try:
        for node_path in nx.all_simple_paths(graph, source, target, cutoff=max_hops):
            edge_path = []
            for a, b in zip(node_path, node_path[1:]):
                edge_data = list(graph.get_edge_data(a, b).values())[0]
                edge_path.append(
                    {
                        "from": a,
                        "to": b,
                        "relation": edge_data["relation_type"],
                        "mechanism": edge_data.get("mechanism"),
                        "evidence_strength": edge_data["evidence_strength"],
                        "limitations": edge_data.get("limitations"),
                        "source_claim_id": edge_data.get("source_claim_id"),
                    }
                )
            paths.append(edge_path)
            if len(paths) >= 5:
                break
    except nx.NetworkXNoPath:
        return []
    return paths
