from __future__ import annotations

from app.models.recommendation import Assessment, Recommendation
from app.schemas.assessment import (
    AssessmentOut,
    ConfidenceOut,
    EvidenceRef,
    MonitoringPlanItem,
    ReasoningPath,
    ReasoningPathStep,
    RecommendationOut,
)


def serialize_recommendation(rec: Recommendation) -> RecommendationOut:
    return RecommendationOut(
        id=rec.id,
        title=rec.title,
        what_to_do=rec.what_to_do,
        why_it_may_work=rec.why_it_may_work,
        impacted_metrics=rec.impacted_metrics,
        time_horizon=rec.time_horizon,
        feasibility_constraints=rec.feasibility_constraints,
        trade_offs=rec.trade_offs,
        confidence=ConfidenceOut(level=rec.confidence_level, reason=rec.confidence_reason),
        evidence=[
            EvidenceRef(
                claim=e.get("claim_text", ""),
                claim_type=e.get("claim_type", "unknown"),
                source_id=e.get("source_id"),
                source_title=e.get("source_title"),
                citation=e.get("citation"),
                excerpt=e.get("excerpt"),
                limitations=e.get("limitations"),
                evidence_status=e.get("evidence_status", "unverified"),
                applicability_note=e.get("applicability_note"),
            )
            for e in rec.evidence
        ],
        monitoring_plan=[
            MonitoringPlanItem(
                metric=m.metric,
                baseline_requirement=m.baseline_requirement,
                target=m.target,
                measurement_method=m.measurement_method,
                measurement_frequency=m.measurement_frequency,
                time_horizon=m.time_horizon,
                unit=m.unit,
                expected_direction=m.expected_direction,
                success_criteria=m.success_criteria,
                uncertainty=m.uncertainty,
            )
            for m in rec.monitoring_plan
        ],
        heuristic_score=rec.heuristic_score,
    )


def serialize_assessment(assessment: Assessment) -> AssessmentOut:
    return AssessmentOut(
        id=assessment.id,
        conversation_id=assessment.conversation_id,
        profile_id=assessment.profile_id,
        version=assessment.version,
        assessment_summary=assessment.assessment_summary,
        known_facts=assessment.known_facts,
        unknowns=assessment.unknowns,
        variables_considered=assessment.variables_considered,
        reasoning_paths=[
            ReasoningPath(
                variables=p.get("variables", []),
                steps=[ReasoningPathStep(**s) for s in p.get("steps", [])],
                narrative=p.get("narrative", ""),
            )
            for p in assessment.reasoning_paths
        ],
        recommendations=[serialize_recommendation(r) for r in assessment.recommendations],
        overall_limitations=assessment.overall_limitations,
        diff_from_previous=assessment.diff_from_previous,
        created_at=assessment.created_at,
    )
