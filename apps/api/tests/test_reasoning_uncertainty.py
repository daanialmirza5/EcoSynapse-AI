import pytest
from app.models.profile import EnvironmentalProfile
from app.models.intervention import Intervention
from app.reasoning.constraints import (
    detect_concerns,
    check_constraints,
    compute_heuristic_score,
    HEURISTIC_WEIGHTS,
)


def test_detect_concerns_extreme_ph_and_moisture():
    profile = EnvironmentalProfile(
        soil_ph=4.2,
        soil_moisture=12.0,
        soil_organic_carbon=0.5,
        rainfall_mm_year=350,
        temperature_c=34.0,
    )
    concerns = detect_concerns(profile)
    keys = {c.key for c in concerns}
    assert "extreme_soil_ph" in keys
    assert "low_soil_moisture" in keys
    assert "low_soil_organic_carbon" in keys
    assert "water_scarcity" in keys
    assert "high_temperature" in keys


def test_check_constraints_water_conflict():
    profile = EnvironmentalProfile(
        rainfall_qualitative="low",
        rainfall_mm_year=400,
        ecosystem_type="arid shrubland",
        constraints=["Limited water budget", "Strict conservation restrictions"],
    )
    intervention = Intervention(
        name="Water Intensive Forestry",
        water_sensitivity="high",
        constraints={"labor_intensive_establishment": True},
        ecosystem_context=["tropical rainforest", "temperate woodland"],
    )
    result = check_constraints(intervention, profile)
    assert result.water_conflict is True
    assert len(result.feasibility_constraints) >= 2
    assert any("arid shrubland" in u for u in result.unknowns)


def test_compute_heuristic_score():
    profile = EnvironmentalProfile(
        rainfall_qualitative="low",
        rainfall_mm_year=400,
        ecosystem_type="arid shrubland",
    )
    intervention = Intervention(
        name="Native Hedgerows",
        water_sensitivity="low",
        constraints={},
        ecosystem_context=["arid shrubland"],
    )
    constraint_result = check_constraints(intervention, profile)
    score = compute_heuristic_score(intervention, "strong", constraint_result, profile)
    assert "total" in score
    assert 0.0 <= score["total"] <= 1.0
    assert score["components"]["evidence_strength"] == 1.0


def test_heuristic_weights_sum_to_one():
    total_weight = sum(HEURISTIC_WEIGHTS.values())
    assert abs(total_weight - 1.0) < 1e-5
