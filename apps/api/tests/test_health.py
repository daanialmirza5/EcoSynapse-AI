def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["knowledge_base"]["sources"] >= 10
    assert body["knowledge_base"]["graph_edges"] >= 10
