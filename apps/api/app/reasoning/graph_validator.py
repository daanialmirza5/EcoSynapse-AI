from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Any


@dataclass
class GraphValidationReport:
    is_valid: bool
    dangling_edges: list[dict[str, str]] = field(default_factory=list)
    self_loops: list[str] = field(default_factory=list)
    cycles_detected: list[list[str]] = field(default_factory=list)
    isolated_nodes: list[str] = field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0


def validate_graph_topology(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> GraphValidationReport:
    """Validates structural integrity of the ecological knowledge/reasoning graph."""
    node_ids = {n.get("id") or n.get("name") for n in nodes if (n.get("id") or n.get("name"))}
    report = GraphValidationReport(
        is_valid=True,
        node_count=len(node_ids),
        edge_count=len(edges),
    )

    adj: dict[str, list[str]] = defaultdict(list)
    connected_nodes: set[str] = set()

    for edge in edges:
        source = edge.get("source_node_id") or edge.get("source")
        target = edge.get("target_node_id") or edge.get("target")

        if not source or not target:
            continue

        if source == target:
            report.self_loops.append(source)
            report.is_valid = False

        if source not in node_ids or target not in node_ids:
            report.dangling_edges.append({"source": str(source), "target": str(target)})
            report.is_valid = False
        else:
            adj[source].append(target)
            connected_nodes.add(source)
            connected_nodes.add(target)

    # Isolated nodes
    report.isolated_nodes = list(node_ids - connected_nodes)

    # Cycle detection using DFS
    visited: dict[str, int] = {}  # 0: unvisited, 1: visiting (in stack), 2: visited
    for node in node_ids:
        visited[node] = 0

    def dfs(curr: str, path: list[str]):
        visited[curr] = 1
        path.append(curr)

        for neighbor in adj.get(curr, []):
            if visited.get(neighbor) == 1:
                # Cycle found
                cycle_start_idx = path.index(neighbor)
                cycle = path[cycle_start_idx:] + [neighbor]
                report.cycles_detected.append(cycle)
            elif visited.get(neighbor) == 0:
                dfs(neighbor, path)

        path.pop()
        visited[curr] = 2

    for node in sorted(node_ids):
        if visited.get(node) == 0:
            dfs(node, [])

    return report


def calculate_node_centrality(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Calculates in-degree, out-degree, and total degree connectivity for ecological nodes."""
    stats: dict[str, dict[str, int]] = {}
    for n in nodes:
        nid = n.get("id") or n.get("name")
        if nid:
            stats[nid] = {"in_degree": 0, "out_degree": 0, "total_degree": 0}

    for edge in edges:
        source = edge.get("source_node_id") or edge.get("source")
        target = edge.get("target_node_id") or edge.get("target")
        if source in stats:
            stats[source]["out_degree"] += 1
            stats[source]["total_degree"] += 1
        if target in stats:
            stats[target]["in_degree"] += 1
            stats[target]["total_degree"] += 1

    return stats
