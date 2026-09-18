def test_retrieval_inspect_returns_trace(client):
    resp = client.post(
        "/api/v1/retrieval/inspect",
        json={"query": "soil organic carbon and microbial activity", "top_k": 3},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["semantic_candidates"] > 0
    assert len(body["results"]) > 0
    top = body["results"][0]
    assert top["source"]["title"]
    assert top["relevance_score"] > 0
    assert len(top["match_reasons"]) > 0

    # Retrieval-channel breakdown: a judge should see how much of the score
    # came from semantic vs. lexical matching, not just a combined number.
    assert "semantic_score" in top and "lexical_score" in top
    assert top["relevance_score"] == round(0.65 * top["semantic_score"] + 0.35 * top["lexical_score"], 4)
    assert any(r["semantic_score"] > 0 or r["lexical_score"] > 0 for r in body["results"])


def test_retrieval_expands_via_knowledge_graph(client):
    resp = client.post(
        "/api/v1/retrieval/inspect",
        json={"query": "monoculture land use", "top_k": 5},
    )
    body = resp.json()
    assert "land_use_monoculture" in body["graph_concepts"]
    assert "habitat_fragmentation" in body["expanded_terms"]


def test_knowledge_graph_endpoint_returns_typed_nodes(client):
    resp = client.get("/api/v1/knowledge/graph")
    body = resp.json()
    node_types = {n["node_type"] for n in body["nodes"]}
    assert "intervention" in node_types
    assert "soil_property" in node_types
    assert len(body["edges"]) > 10


def test_sources_endpoint_lists_verified_sources(client):
    resp = client.get("/api/v1/knowledge/sources")
    sources = resp.json()
    assert len(sources) >= 10
    assert all(s["is_verified"] for s in sources)
    assert any(s["doi"] for s in sources)
