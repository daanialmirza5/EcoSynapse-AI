"""Concern detection and the constraint / trade-off / heuristic-scoring engine.

The scoring produced here is explicitly a *prototype decision-support
heuristic* — a transparent weighted sum over a handful of named factors — and
must never be presented as a validated or universal biodiversity index.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.models.intervention import Intervention
from app.models.profile import EnvironmentalProfile

CONCERN_TO_INTERVENTIONS: dict[str, list[str]] = {
    "low_soil_organic_carbon": ["cover_cropping_soil_organic_matter_management", "agroforestry"],
    "low_soil_moisture": ["water_harvesting_soil_moisture_conservation"],
    "water_scarcity": ["water_harvesting_soil_moisture_conservation"],
    "monoculture_land_use": ["crop_diversification_intercropping", "agroforestry", "native_hedgerow_habitat_strips"],
    "pesticide_pressure": ["integrated_pest_management"],
    "deforestation_pressure": ["agroforestry", "native_hedgerow_habitat_strips"],
    "declining_biodiversity": [
        "agroforestry", "crop_diversification_intercropping",
        "native_hedgerow_habitat_strips", "integrated_pest_management",
    ],
    "high_temperature": ["water_harvesting_soil_moisture_conservation"],
}

CONCERN_TO_NODE: dict[str, str] = {
    "low_soil_organic_carbon": "soil_organic_carbon",
    "extreme_soil_ph": "soil_ph",
    "low_soil_moisture": "soil_moisture",
    "water_scarcity": "rainfall",
    "monoculture_land_use": "land_use_monoculture",
    "pesticide_pressure": "pesticide_use",
    "deforestation_pressure": "deforestation",
    "declining_biodiversity": "species_richness",
    "high_temperature": "temperature",
}

CONCERN_EXPLANATIONS: dict[str, str] = {
    "low_soil_organic_carbon": "Soil organic carbon is below 1%, a level commonly associated with degraded soil biological activity.",
    "low_soil_moisture": "Reported soil moisture is low, which can limit vegetation establishment.",
    "water_scarcity": "Rainfall is reported as low or below 500 mm/year, constraining water-demanding interventions.",
    "monoculture_land_use": "Land use is a monoculture, which the literature associates with reduced landscape heterogeneity.",
    "pesticide_pressure": "Pesticide use was reported, a documented hazard to non-target invertebrates.",
    "deforestation_pressure": "Deforestation pressure was reported near or on this land.",
    "declining_biodiversity": "A declining biodiversity trend was reported by the user.",
    "extreme_soil_ph": "Soil pH is outside the 5.5-8.5 range commonly associated with healthy microbial activity; no cataloged intervention in this demo directly targets pH.",
    "high_temperature": (
        "Temperature is reported above 30°C. Elevated temperature combined with limited water availability "
        "increases heat and moisture stress on vegetation and is associated with species range shifts (see source "
        "s8); water-retention interventions may help buffer soil moisture under these conditions, though this is a "
        "general inference rather than a source-specific test of temperature mitigation."
    ),
}


@dataclass
class DetectedConcern:
    key: str
    explanation: str


def detect_concerns(profile: EnvironmentalProfile) -> list[DetectedConcern]:
    concerns: list[str] = []
    if profile.soil_organic_carbon is not None and profile.soil_organic_carbon < 1.0:
        concerns.append("low_soil_organic_carbon")
    if profile.soil_ph is not None and (profile.soil_ph < 5.5 or profile.soil_ph > 8.5):
        concerns.append("extreme_soil_ph")
    if profile.soil_moisture is not None and profile.soil_moisture < 20:
        concerns.append("low_soil_moisture")
    if profile.rainfall_qualitative == "low" or (
        profile.rainfall_mm_year is not None and profile.rainfall_mm_year < 500
    ):
        concerns.append("water_scarcity")
    if profile.land_use_type and "monoculture" in profile.land_use_type.lower():
        concerns.append("monoculture_land_use")
    if profile.human_impact_indicators.get("pesticide_use"):
        concerns.append("pesticide_pressure")
    if profile.human_impact_indicators.get("deforestation"):
        concerns.append("deforestation_pressure")
    if profile.biodiversity_indicators.get("reported_trend") == "declining":
        concerns.append("declining_biodiversity")
    if profile.temperature_c is not None and profile.temperature_c > 30:
        concerns.append("high_temperature")
    return [DetectedConcern(key=c, explanation=CONCERN_EXPLANATIONS.get(c, c)) for c in concerns]


@dataclass
class ConstraintCheckResult:
    feasibility_constraints: list[str] = field(default_factory=list)
    trade_offs: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    water_conflict: bool = False


def check_constraints(intervention: Intervention, profile: EnvironmentalProfile) -> ConstraintCheckResult:
    result = ConstraintCheckResult()
    water_scarce = profile.rainfall_qualitative == "low" or (
        profile.rainfall_mm_year is not None and profile.rainfall_mm_year < 500
    )
    if water_scarce and intervention.water_sensitivity in ("medium", "high"):
        result.water_conflict = intervention.water_sensitivity == "high"
        result.feasibility_constraints.append(
            f"This intervention has {intervention.water_sensitivity} water sensitivity during establishment; "
            "the profile reports low rainfall, so irrigation or staged/drought-tolerant establishment should be "
            "planned for and monitored."
        )
        result.unknowns.append("Local irrigation access / water budget was not provided.")

    for user_constraint in profile.constraints or []:
        uc = user_constraint.lower()
        if "budget" in uc and intervention.constraints.get("labor_intensive_establishment"):
            result.feasibility_constraints.append(
                f"User indicated '{user_constraint}'; this intervention was flagged as labor-intensive to establish."
            )
        if "irrigation" in uc or "water" in uc:
            result.feasibility_constraints.append(
                f"User indicated '{user_constraint}', reinforcing the water-availability caution above."
            )
        if "conservation restriction" in uc or "protected area" in uc:
            result.feasibility_constraints.append(
                f"User indicated '{user_constraint}'; verify this intervention is permitted under local conservation rules before implementation."
            )

    if not profile.biodiversity_indicators:
        result.unknowns.append("No biodiversity baseline was reported, so improvement cannot be measured against a starting point.")
    if intervention.ecosystem_context and profile.ecosystem_type:
        if not any(profile.ecosystem_type.lower() in ctx.lower() or ctx.lower() in profile.ecosystem_type.lower()
                   for ctx in intervention.ecosystem_context):
            result.unknowns.append(
                f"The cited evidence for this intervention was studied in {', '.join(intervention.ecosystem_context)}; "
                f"applicability to a '{profile.ecosystem_type}' ecosystem is not directly confirmed."
            )
    return result


HEURISTIC_WEIGHTS = {
    "evidence_strength": 0.4,
    "constraint_fit": 0.35,
    "context_match": 0.25,
}

_EVIDENCE_STRENGTH_SCORE = {"strong": 1.0, "moderate": 0.65, "weak": 0.35, "hypothesis": 0.15}


def compute_heuristic_score(
    intervention: Intervention,
    avg_evidence_strength: str,
    constraint_result: ConstraintCheckResult,
    profile: EnvironmentalProfile,
) -> dict:
    evidence_component = _EVIDENCE_STRENGTH_SCORE.get(avg_evidence_strength, 0.15)
    constraint_component = 1.0
    if constraint_result.water_conflict:
        constraint_component -= 0.5
    constraint_component -= 0.15 * len(constraint_result.feasibility_constraints)
    constraint_component = max(0.0, min(1.0, constraint_component))

    context_component = 1.0
    if intervention.ecosystem_context and profile.ecosystem_type:
        matched = any(
            profile.ecosystem_type.lower() in ctx.lower() or ctx.lower() in profile.ecosystem_type.lower()
            for ctx in intervention.ecosystem_context
        )
        context_component = 1.0 if matched else 0.5
    elif not profile.ecosystem_type:
        context_component = 0.6

    total = (
        HEURISTIC_WEIGHTS["evidence_strength"] * evidence_component
        + HEURISTIC_WEIGHTS["constraint_fit"] * constraint_component
        + HEURISTIC_WEIGHTS["context_match"] * context_component
    )
    return {
        "label": "prototype_decision_support_heuristic",
        "disclaimer": "Not a validated or universal biodiversity index — a transparent weighted heuristic for ranking candidates in this demo only.",
        "weights": HEURISTIC_WEIGHTS,
        "components": {
            "evidence_strength": round(evidence_component, 3),
            "constraint_fit": round(constraint_component, 3),
            "context_match": round(context_component, 3),
        },
        "total": round(total, 3),
    }
