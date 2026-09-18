"""Regression test for a real bug found during Docker/Postgres verification:
``monitoring_plans.unit`` was declared ``String(40)``, which SQLite never
enforces (so the whole sqlite-backed suite passed) but Postgres does --
`generate_monitoring_entry`'s real habitat_diversity unit text
("structural/habitat diversity index (method-dependent)", 55 chars) caused
a StringDataRightTruncation error in production. Fixed by widening
`unit`/`measurement_frequency` to unbounded Text (see migration
4aca730fbe84). This test inserts a MonitoringPlan directly with long values
so it fails regardless of which database backend the suite happens to run
against.
"""
from __future__ import annotations

from app.models.monitoring import MonitoringPlan
from app.models.recommendation import Assessment, Recommendation
from app.models.profile import EnvironmentalProfile


def test_monitoring_plan_accepts_long_unit_and_frequency_text(db_session):
    profile = EnvironmentalProfile(name="width test profile")
    db_session.add(profile)
    db_session.flush()

    assessment = Assessment(profile_id=profile.id, assessment_summary="x", version=1)
    db_session.add(assessment)
    db_session.flush()

    rec = Recommendation(
        assessment_id=assessment.id,
        profile_id=profile.id,
        title="x",
        what_to_do="x",
        why_it_may_work="x",
    )
    db_session.add(rec)
    db_session.flush()

    long_unit = "structural/habitat diversity index (method-dependent, exceeds forty characters)"
    long_frequency = "Seasonally or annually, with consistent survey effort across all fixed plots and observers"
    assert len(long_unit) > 40
    assert len(long_frequency) > 80

    plan = MonitoringPlan(
        recommendation_id=rec.id,
        metric="habitat_diversity",
        baseline_requirement="x",
        measurement_method="x",
        measurement_frequency=long_frequency,
        unit=long_unit,
    )
    db_session.add(plan)
    db_session.commit()  # would raise DataError/StringDataRightTruncation on Postgres if columns regress

    db_session.refresh(plan)
    assert plan.unit == long_unit
    assert plan.measurement_frequency == long_frequency
