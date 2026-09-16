def _make_demo_profile(client):
    return client.post(
        "/api/v1/profiles",
        json={
            "name": "Demo semi-arid wheat",
            "region": "Illustrative semi-arid region",
            "ecosystem_type": "semi-arid",
            "land_use_type": "monoculture wheat cropland",
            "soil_organic_carbon": 0.3,
            "rainfall_qualitative": "low",
            "biodiversity_indicators": {"reported_trend": "declining"},
        },
    ).json()


def test_insufficient_variables_returns_explicit_limitation(client):
    profile = client.post("/api/v1/profiles", json={"name": "Barely anything known"}).json()
    resp = client.post("/api/v1/assessments", json={"profile_id": profile["id"]})
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["recommendations"]) == 0
    assert any("Evidence is insufficient" in lim for lim in body["overall_limitations"])


def test_demo_scenario_produces_grounded_recommendations(client):
    profile = _make_demo_profile(client)
    resp = client.post("/api/v1/assessments", json={"profile_id": profile["id"]})
    assert resp.status_code == 201
    body = resp.json()

    assert len(body["variables_considered"]) >= 3
    assert len(body["recommendations"]) > 0

    for rec in body["recommendations"]:
        assert rec["time_horizon"] in ("short", "medium", "long")
        assert rec["confidence"]["level"] in ("low", "medium", "high")
        assert isinstance(rec["impacted_metrics"], list) and rec["impacted_metrics"]
        assert isinstance(rec["monitoring_plan"], list) and rec["monitoring_plan"]
        for entry in rec["monitoring_plan"]:
            # No fabricated numeric targets: target is always a baseline-first
            # statement or an explicit comparison-to-baseline statement.
            assert "target" not in entry or entry["target"] is None or "baseline" in entry["target"].lower()
        for ev in rec["evidence"]:
            assert ev["evidence_status"] in (
                "supported", "partially_supported", "insufficient_evidence", "unverified",
            )
            if ev["claim_type"] == "hypothesis":
                assert ev["evidence_status"] == "insufficient_evidence"


def test_agroforestry_recommendation_is_not_overclaimed(client):
    profile = _make_demo_profile(client)
    body = client.post("/api/v1/assessments", json={"profile_id": profile["id"]}).json()
    agroforestry = next((r for r in body["recommendations"] if "Agroforestry" in r["title"]), None)
    assert agroforestry is not None
    combined_text = agroforestry["why_it_may_work"] + " ".join(agroforestry["trade_offs"])
    assert "no unequivocal effect" in combined_text.lower() or "inconsistent" in combined_text.lower()
    assert agroforestry["confidence"]["level"] == "low"


def test_reassess_reflects_profile_change(client):
    profile = _make_demo_profile(client)
    first = client.post("/api/v1/assessments", json={"profile_id": profile["id"]}).json()

    client.patch(f"/api/v1/profiles/{profile['id']}", json={"soil_ph": 7.0})
    second = client.post(f"/api/v1/assessments/{first['id']}/reassess").json()

    assert second["version"] == first["version"] + 1
    assert any(d.get("field") == "soil_ph" for d in second["diff_from_previous"])


def test_export_returns_full_payload(client):
    profile = _make_demo_profile(client)
    assessment = client.post("/api/v1/assessments", json={"profile_id": profile["id"]}).json()
    resp = client.get(f"/api/v1/assessments/{assessment['id']}/export")
    assert resp.status_code == 200
    assert resp.json()["id"] == assessment["id"]
