"""A small, prototype scientific-evaluation benchmark.

This is explicitly a prototype evaluation with hand-curated cases and
automated structural checks -- NOT an expert-labeled benchmark with human
relevance judgments. It exercises the properties listed in the challenge's
evaluation section that can be checked automatically: multi-variable
coverage, missing-information detection, output schema validity, citation
coverage, and unsupported-claim rate. See docs/evaluation.md for the full
methodology and its limitations.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _cases_dir() -> Path:
    # apps/api/tests/test_evaluation_benchmark.py -> repo_root/tests/evaluation_cases
    return Path(__file__).resolve().parents[3] / "tests" / "evaluation_cases"


def _load_cases() -> list[dict]:
    cases = []
    for path in sorted(_cases_dir().glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            cases.append(json.load(f))
    return cases


CASES = _load_cases()


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_evaluation_case(client, case):
    profile = client.post("/api/v1/profiles", json=case["profile"]).json()
    for obs in case.get("observations", []):
        obs_resp = client.post(f"/api/v1/profiles/{profile['id']}/observations", json=obs)
        assert obs_resp.status_code == 201, f"failed to seed observation for case {case['id']}: {obs_resp.text}"
    assessment = client.post("/api/v1/assessments", json={"profile_id": profile["id"]}).json()
    expect = case["expect"]

    # Multi-variable coverage
    assert len(assessment["variables_considered"]) >= expect["min_variables_considered"]

    # Missing-information detection: the insufficient-data gate must fire
    # exactly when expected, never silently producing a shallow answer.
    is_insufficient = len(assessment["recommendations"]) == 0 and any(
        "Evidence is insufficient" in lim for lim in assessment["overall_limitations"]
    )
    if expect["insufficient_data_expected"]:
        assert is_insufficient, "Expected the insufficient-data gate to fire for this case"
    else:
        assert not is_insufficient, "Did not expect the insufficient-data gate to fire for this case"

    assert len(assessment["recommendations"]) >= expect["min_recommendations"]

    # Output schema validity: every recommendation has the mandated fields
    # non-empty/well-formed (challenge section 14 contract).
    for rec in assessment["recommendations"]:
        assert rec["time_horizon"] in ("short", "medium", "long")
        assert rec["confidence"]["level"] in ("low", "medium", "high")
        assert rec["evidence_strength_summary"] in ("strong", "moderate", "weak", "hypothesis")
        assert 0.0 <= rec["data_completeness"] <= 1.0
        assert rec["impacted_metrics"]
        assert rec["monitoring_plan"]

        # Citation coverage: every source_supported claim must carry a citation.
        for ev in rec["evidence"]:
            if ev["claim_type"] == "source_supported":
                assert ev["citation"], f"source_supported claim missing citation: {ev['claim']}"
            # Unsupported-claim rate: hypothesis/unknown claims must never be
            # reported as fully "supported".
            if ev["claim_type"] in ("hypothesis", "unknown"):
                assert ev["evidence_status"] == "insufficient_evidence"

    if expect["must_mention_any_recommendation_title_containing"]:
        titles = " | ".join(r["title"] for r in assessment["recommendations"])
        assert any(kw.lower() in titles.lower() for kw in expect["must_mention_any_recommendation_title_containing"])

    # Ecosystem-context mismatches must be surfaced, not silently ignored.
    if expect.get("expect_ecosystem_mismatch_note"):
        all_text = " ".join(
            note
            for rec in assessment["recommendations"]
            for note in rec["trade_offs"] + [e.get("applicability_note") or "" for e in rec["evidence"]]
        )
        assert "ecosystem" in all_text.lower() or "context" in all_text.lower(), (
            "Expected at least one recommendation to flag an ecosystem/context mismatch"
        )

    # A recorded baseline must change the monitoring plan's baseline_requirement
    # wording for that metric, without ever inventing a numeric target.
    metric_to_check = expect.get("expect_baseline_recorded_for_metric")
    if metric_to_check:
        matching_entries = [
            m
            for rec in assessment["recommendations"]
            for m in rec["monitoring_plan"]
            if m["metric"] == metric_to_check
        ]
        assert matching_entries, f"Expected a monitoring plan entry for {metric_to_check}"
        for entry in matching_entries:
            assert "baseline" in entry["baseline_requirement"].lower()
            assert "recorded" in entry["baseline_requirement"].lower() or "already" in entry["baseline_requirement"].lower()
            assert entry["target"] is None or "establish a baseline first" not in entry["target"].lower()


def test_high_temperature_is_detected_as_a_concern(client):
    # Regression guard for a real gap found while compiling the knowledge
    # coverage matrix: temperature (a mandatory climate factor) previously
    # had no concern-detection rule at all -- it was tracked as a "known
    # variable" but never independently triggered any candidate intervention.
    profile = client.post(
        "/api/v1/profiles",
        json={
            "name": "Heat stress check",
            "ecosystem_type": "semi-arid",
            "temperature_c": 35,
            "rainfall_qualitative": "low",
            "biodiversity_indicators": {"reported_trend": "declining"},
        },
    ).json()
    assessment = client.post("/api/v1/assessments", json={"profile_id": profile["id"]}).json()
    assert "high temperature" in assessment["assessment_summary"].lower() or "temperature" in assessment["assessment_summary"].lower()


def test_benchmark_has_multiple_curated_cases():
    # Guards against the benchmark silently losing coverage.
    assert len(CASES) >= 3
