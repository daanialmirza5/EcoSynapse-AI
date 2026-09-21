import pytest
from app.reasoning.graph_validator import validate_graph_topology, calculate_node_centrality


def test_valid_graph_topology():
    nodes = [{"id": "soil_carbon"}, {"id": "microbial_activity"}, {"id": "crop_yield"}]
    edges = [
        {"source": "soil_carbon", "target": "microbial_activity"},
        {"source": "microbial_activity", "target": "crop_yield"},
    ]
    report = validate_graph_topology(nodes, edges)
    assert report.is_valid is True
    assert len(report.dangling_edges) == 0
    assert len(report.self_loops) == 0
    assert len(report.cycles_detected) == 0
    assert len(report.isolated_nodes) == 0


def test_dangling_edge_and_self_loop_detection():
    nodes = [{"id": "tree_canopy"}, {"id": "soil_moisture"}]
    edges = [
        {"source": "tree_canopy", "target": "tree_canopy"},  # self loop
        {"source": "tree_canopy", "target": "unknown_node"},  # dangling edge
    ]
    report = validate_graph_topology(nodes, edges)
    assert report.is_valid is False
    assert "tree_canopy" in report.self_loops
    assert len(report.dangling_edges) == 1
    assert report.dangling_edges[0]["target"] == "unknown_node"


def test_cycle_detection():
    nodes = [{"id": "A"}, {"id": "B"}, {"id": "C"}]
    edges = [
        {"source": "A", "target": "B"},
        {"source": "B", "target": "C"},
        {"source": "C", "target": "A"},
    ]
    report = validate_graph_topology(nodes, edges)
    assert len(report.cycles_detected) >= 1
    assert report.cycles_detected[0] == ["A", "B", "C", "A"]


def test_node_centrality():
    nodes = [{"id": "hub"}, {"id": "leaf1"}, {"id": "leaf2"}]
    edges = [
        {"source": "hub", "target": "leaf1"},
        {"source": "hub", "target": "leaf2"},
    ]
    centrality = calculate_node_centrality(nodes, edges)
    assert centrality["hub"]["out_degree"] == 2
    assert centrality["hub"]["in_degree"] == 0
    assert centrality["hub"]["total_degree"] == 2
    assert centrality["leaf1"]["in_degree"] == 1
