from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ConfidenceLevel, TimeHorizon


class AssessmentCreate(BaseModel):
    profile_id: str
    conversation_id: str | None = None
    focus_question: str | None = Field(
        default=None, description="Optional natural-language question to focus the assessment on."
    )


class ConfidenceOut(BaseModel):
    level: ConfidenceLevel
    reason: str


class EvidenceRef(BaseModel):
    claim: str
    claim_type: str
    source_id: str | None
    source_title: str | None
    citation: str | None
    excerpt: str | None
    limitations: str | None
    evidence_status: str
    applicability_note: str | None = None


class MonitoringPlanItem(BaseModel):
    metric: str
    baseline_requirement: str
    target: str | None
    measurement_method: str
    measurement_frequency: str
    time_horizon: TimeHorizon
    unit: str | None
    expected_direction: str | None
    success_criteria: str | None
    uncertainty: str | None


class RecommendationOut(BaseModel):
    id: str
    intervention_id: str | None = Field(
        default=None,
        description="Links this recommendation to its knowledge-graph node id, so a caller can find the "
        "exact reasoning-path entries (in AssessmentOut.reasoning_paths) that produced it.",
    )
    title: str
    what_to_do: str
    why_it_may_work: str
    impacted_metrics: list[str]
    time_horizon: TimeHorizon
    feasibility_constraints: list[str]
    trade_offs: list[str]
    confidence: ConfidenceOut
    evidence_strength_summary: str = Field(
        description="Raw average evidence-strength label (strong/moderate/weak/hypothesis) behind the "
        "confidence judgement above -- kept distinct so a caller can see the underlying evidence quality "
        "separately from how constraints/context adjusted the final confidence."
    )
    data_completeness: float = Field(
        ge=0, le=1, description="Fraction of core profile fields known at assessment time (see clarify.py)."
    )
    evidence: list[EvidenceRef]
    monitoring_plan: list[MonitoringPlanItem]
    heuristic_score: dict[str, Any] = Field(default_factory=dict)


class ReasoningPathStep(BaseModel):
    from_node: str
    relation: str
    to_node: str
    evidence_strength: str
    source_claim_id: str | None = None


class ReasoningPath(BaseModel):
    variables: list[str]
    steps: list[ReasoningPathStep]
    narrative: str


class AssessmentOut(BaseModel):
    id: str
    conversation_id: str | None
    profile_id: str
    version: int
    assessment_summary: str
    known_facts: list[dict[str, Any]]
    unknowns: list[str]
    variables_considered: list[str]
    reasoning_paths: list[ReasoningPath]
    recommendations: list[RecommendationOut]
    overall_limitations: list[str]
    diff_from_previous: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
