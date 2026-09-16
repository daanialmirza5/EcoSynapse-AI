def test_ambiguous_message_triggers_clarifying_questions(client):
    conv = client.post("/api/v1/conversations", json={"title": "t1"}).json()
    resp = client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        json={"content": "Biodiversity is declining on my land."},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready_for_assessment"] is False
    assert len(body["clarifying_questions"]) > 0
    assert len(body["clarifying_questions"]) <= 3


def test_structured_facts_extracted_and_marked_ready(client):
    conv = client.post("/api/v1/conversations", json={"title": "t2"}).json()
    resp = client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        json={
            "content": "It is a semi-arid region with monoculture wheat cropland, low rainfall, "
            "soil organic carbon 0.3%."
        },
    )
    body = resp.json()
    assert body["extracted_fields"]["soil_organic_carbon"] == 0.3
    assert body["extracted_fields"]["rainfall_qualitative"] == "low"
    assert body["extracted_fields"]["ecosystem_type"] == "semi-arid"
    assert body["ready_for_assessment"] is True


def test_conflicting_value_is_flagged(client):
    conv = client.post("/api/v1/conversations", json={"title": "t3"}).json()
    client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        json={"content": "Soil pH is 6.5."},
    )
    resp = client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        json={"content": "Soil pH is 8.0."},
    )
    body = resp.json()
    assert any(c["field"] == "soil_ph" for c in body["conflicts"])


def test_structured_input_merges_into_profile(client):
    conv = client.post("/api/v1/conversations", json={"title": "t4"}).json()
    resp = client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        json={
            "content": "Here is our data.",
            "structured_input": {"soil_ph": 6.8, "region": "Test Valley"},
        },
    )
    body = resp.json()
    profile = client.get(f"/api/v1/profiles/{body['profile_id']}").json()
    assert profile["soil_ph"] == 6.8
    assert profile["region"] == "Test Valley"
