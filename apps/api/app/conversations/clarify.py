"""Missing-information detection and clarifying-question generation.

Implements the "ask a few high-value questions, not everything at once"
behaviour required by the challenge: fields are ranked by priority and only
the top ``max_questions`` unanswered ones are surfaced per turn.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.profile import EnvironmentalProfile

CORE_FIELDS = [
    "region_or_ecosystem",
    "land_use_type",
    "rainfall",
    "soil_organic_carbon",
    "soil_ph",
    "soil_moisture",
    "biodiversity_indicators",
    "human_impact_indicators",
    "temperature_c",
]

_QUESTION_BANK: dict[str, tuple[str, str, int]] = {
    "region_or_ecosystem": (
        "What region or ecosystem type is this land in (e.g. semi-arid, tropical, temperate grassland)?",
        "Region/ecosystem determines which ecological relationships and evidence are applicable.",
        1,
    ),
    "land_use_type": (
        "What is the current land use (e.g. monoculture crop, pasture, forest, mixed cropland)?",
        "Land use is a primary driver of habitat fragmentation and biodiversity outcomes.",
        1,
    ),
    "rainfall": (
        "What are the rainfall conditions — roughly how much annual rainfall (mm), or would you describe it as low, medium, or high?",
        "Water availability constrains which interventions (e.g. new tree planting) are feasible.",
        2,
    ),
    "soil_organic_carbon": (
        "Do you know the soil organic carbon content (%), if it has been measured?",
        "Soil organic carbon links directly to soil biological activity and long-term fertility.",
        2,
    ),
    "soil_ph": (
        "What is the soil pH, if known?",
        "Extreme pH can constrain soil biological activity and which interventions will work.",
        3,
    ),
    "soil_moisture": (
        "Do you have a soil moisture measurement, or is it just visibly dry/wet?",
        "Soil moisture affects vegetation establishment success for many interventions.",
        3,
    ),
    "biodiversity_indicators": (
        "What biodiversity change have you observed — e.g. fewer pollinators, declining species, or no clear change?",
        "This is the outcome we are trying to improve, so a baseline observation matters.",
        1,
    ),
    "human_impact_indicators": (
        "Are there pollution, pesticide use, or deforestation pressures on or near this land?",
        "Human pressures can offset or block the benefit of any intervention.",
        3,
    ),
    "temperature_c": (
        "What is the typical temperature range for this location, if known?",
        "Temperature interacts with rainfall to determine climate suitability for interventions.",
        4,
    ),
}


@dataclass
class ClarifyingQuestion:
    field: str
    question: str
    reason: str
    priority: int


def missing_fields(profile: EnvironmentalProfile) -> list[str]:
    missing: list[str] = []
    if not profile.region and not profile.ecosystem_type:
        missing.append("region_or_ecosystem")
    if not profile.land_use_type:
        missing.append("land_use_type")
    if profile.rainfall_mm_year is None and not profile.rainfall_qualitative:
        missing.append("rainfall")
    if profile.soil_organic_carbon is None:
        missing.append("soil_organic_carbon")
    if profile.soil_ph is None:
        missing.append("soil_ph")
    if profile.soil_moisture is None:
        missing.append("soil_moisture")
    if not profile.biodiversity_indicators:
        missing.append("biodiversity_indicators")
    if not profile.human_impact_indicators:
        missing.append("human_impact_indicators")
    if profile.temperature_c is None:
        missing.append("temperature_c")
    return missing


def known_core_variable_count(profile: EnvironmentalProfile) -> int:
    checks = [
        profile.soil_ph is not None,
        profile.soil_organic_carbon is not None,
        profile.soil_moisture is not None,
        profile.rainfall_mm_year is not None or profile.rainfall_qualitative is not None,
        profile.temperature_c is not None,
        profile.land_use_type is not None,
        bool(profile.biodiversity_indicators),
        bool(profile.human_impact_indicators),
    ]
    return sum(checks)


def profile_completeness(profile: EnvironmentalProfile) -> float:
    total = len(CORE_FIELDS)
    missing = len(missing_fields(profile))
    return round((total - missing) / total, 2)


def generate_clarifying_questions(profile: EnvironmentalProfile, max_questions: int = 3) -> list[ClarifyingQuestion]:
    missing = missing_fields(profile)
    candidates = [
        ClarifyingQuestion(field=f, question=_QUESTION_BANK[f][0], reason=_QUESTION_BANK[f][1], priority=_QUESTION_BANK[f][2])
        for f in missing
        if f in _QUESTION_BANK
    ]
    candidates.sort(key=lambda q: q.priority)
    return candidates[:max_questions]


def ready_for_assessment(profile: EnvironmentalProfile) -> bool:
    return known_core_variable_count(profile) >= 3
