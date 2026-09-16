"""Monitoring-plan generation.

Never invents a numeric target: a target is only stated when a user-reported
baseline observation exists for that metric, and even then it is framed as
"compare against baseline", not a fabricated improvement percentage.
"""
from __future__ import annotations

from dataclasses import dataclass

_METRIC_TEMPLATES: dict[str, dict[str, str]] = {
    "soil_organic_carbon": {
        "unit": "%",
        "measurement_method": "Laboratory soil test (e.g. dry combustion or Walkley-Black method) on composite samples from a consistent depth (e.g. 0-15cm).",
        "measurement_frequency": "Annually, same season each year.",
    },
    "soil_moisture": {
        "unit": "% volumetric water content",
        "measurement_method": "Field soil moisture probe or gravimetric sampling at a fixed set of georeferenced points.",
        "measurement_frequency": "Monthly during the growing season.",
    },
    "soil_ph": {
        "unit": "pH",
        "measurement_method": "Standard soil pH test (1:2.5 soil:water) on composite samples.",
        "measurement_frequency": "Annually.",
    },
    "habitat_diversity": {
        "unit": "structural/habitat diversity index (method-dependent)",
        "measurement_method": "Structured vegetation/habitat-structure survey (e.g. point-intercept or transect method) at fixed plots.",
        "measurement_frequency": "Annually, same season.",
    },
    "species_richness": {
        "unit": "count of species observed",
        "measurement_method": "Standardized species survey (e.g. transect or point-count) by a consistent observer/protocol at fixed plots.",
        "measurement_frequency": "Seasonally or annually, with consistent survey effort.",
    },
    "beneficial_arthropod_abundance": {
        "unit": "count per trap/sample",
        "measurement_method": "Standardized trapping (e.g. pitfall or sticky traps) at fixed points.",
        "measurement_frequency": "Multiple times per growing season.",
    },
    "vegetation_establishment": {
        "unit": "% survival / % cover",
        "measurement_method": "Establishment and survival counts of planted individuals at fixed plots.",
        "measurement_frequency": "At 3, 6, and 12 months after planting.",
    },
    "pesticide_use": {
        "unit": "applications per season",
        "measurement_method": "Farm input records of pesticide applications (product, dose, timing).",
        "measurement_frequency": "Per application, summarized seasonally.",
    },
}

_DEFAULT_TEMPLATE = {
    "unit": "context-dependent",
    "measurement_method": "Consistent, repeatable field observation or sampling protocol appropriate to this metric.",
    "measurement_frequency": "Regularly, at a fixed interval appropriate to the metric's rate of change.",
}


@dataclass
class MonitoringPlanEntry:
    metric: str
    baseline_requirement: str
    target: str | None
    measurement_method: str
    measurement_frequency: str
    time_horizon: str
    unit: str
    expected_direction: str | None
    success_criteria: str | None
    uncertainty: str | None


def generate_monitoring_entry(
    metric: str,
    time_horizon: str,
    expected_direction: str | None,
    has_baseline_observation: bool,
) -> MonitoringPlanEntry:
    template = _METRIC_TEMPLATES.get(metric, _DEFAULT_TEMPLATE)

    if has_baseline_observation:
        target = "Compare future measurements against the recorded baseline observation; a specific numeric improvement target is not established by current evidence."
        baseline_requirement = "Baseline already recorded for this profile; continue measuring with the same method for comparability."
    else:
        target = "Establish a baseline first; a defensible target cannot be determined from the current information."
        baseline_requirement = "No baseline observation recorded yet for this metric — record one before evaluating change."

    success_criteria = None
    uncertainty = "Natural variability and measurement method changes can obscure real trends; keep method and timing consistent."
    if expected_direction:
        success_criteria = (
            f"A sustained {expected_direction} in {metric.replace('_', ' ')} across at least two consecutive "
            "monitoring cycles, beyond normal seasonal variability, would be consistent with (not proof of) the "
            "intervention having an effect."
        )
    else:
        uncertainty += " Directional expectation is not established by current evidence for this metric/intervention pairing."

    return MonitoringPlanEntry(
        metric=metric,
        baseline_requirement=baseline_requirement,
        target=target,
        measurement_method=template["measurement_method"],
        measurement_frequency=template["measurement_frequency"],
        time_horizon=time_horizon,
        unit=template["unit"],
        expected_direction=expected_direction,
        success_criteria=success_criteria,
        uncertainty=uncertainty,
    )
