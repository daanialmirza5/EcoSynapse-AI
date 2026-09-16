"""The multi-metric reasoning pipeline (challenge section 11, steps 1-10).

build environmental state -> identify variables -> find KG relationships ->
gather evidence -> generate candidate interventions -> check constraints ->
identify trade-offs -> build structured recommendations -> verify claims ->
generate monitoring plans.

Everything here is deterministic and traceable back to either a database row
(claim/source/edge) or an explicit, labeled heuristic/hypothesis. No step
calls an LLM to invent facts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.evidence.verification import verify_claim
from app.knowledge.graph import build_graph, find_paths
from app.models.evidence import EvidenceChunk, ScientificClaim, ScientificSource
from app.models.intervention import Intervention
from app.models.knowledge import KnowledgeEdge
from app.models.profile import EnvironmentalObservation, EnvironmentalProfile
from app.models.recommendation import Assessment, Recommendation
from app.monitoring.plans import generate_monitoring_entry
from app.reasoning.constraints import (
    CONCERN_TO_INTERVENTIONS,
    CONCERN_TO_NODE,
    check_constraints,
    compute_heuristic_score,
    detect_concerns,
)

_STRENGTH_RANK = {"strong": 3, "moderate": 2, "weak": 1, "hypothesis": 0}
_RANK_TO_STRENGTH = {v: k for k, v in _STRENGTH_RANK.items()}

INSUFFICIENT_VARIABLES_MESSAGE = (
    "Fewer than three environmental variables are currently known for this profile. "
    "Evidence is insufficient to support a reliable quantitative estimate for this condition; "
    "answer the clarifying questions or provide more profile detail before requesting a full assessment."
)


@dataclass
class ReasoningPathOut:
    variables: list[str]
    steps: list[dict[str, Any]]
    narrative: str


@dataclass
class RecommendationBuild:
    intervention: Intervention
    title: str
    what_to_do: str
    why_it_may_work: str
    impacted_metrics: list[str]
    time_horizon: str
    feasibility_constraints: list[str]
    trade_offs: list[str]
    confidence_level: str
    confidence_reason: str
    evidence: list[dict[str, Any]]
    heuristic_score: dict[str, Any]
    monitoring_plan: list[dict[str, Any]]


def _known_facts(profile: EnvironmentalProfile) -> list[dict[str, Any]]:
    facts = []
    scalar_units = {
        "soil_ph": None, "soil_organic_carbon": "%", "soil_moisture": "%",
        "rainfall_mm_year": "mm/year", "temperature_c": "°C",
    }
    for field_name, unit in scalar_units.items():
        value = getattr(profile, field_name, None)
        if value is not None:
            facts.append({"field": field_name, "value": value, "unit": unit, "source": "user_provided"})
    for field_name in ("region", "ecosystem_type", "land_use_type", "rainfall_qualitative"):
        value = getattr(profile, field_name, None)
        if value:
            facts.append({"field": field_name, "value": value, "unit": None, "source": "user_provided"})
    if profile.biodiversity_indicators:
        facts.append({"field": "biodiversity_indicators", "value": profile.biodiversity_indicators, "unit": None, "source": "user_provided"})
    if profile.human_impact_indicators:
        facts.append({"field": "human_impact_indicators", "value": profile.human_impact_indicators, "unit": None, "source": "user_provided"})
    return facts


def _variables_considered(profile: EnvironmentalProfile) -> list[str]:
    variables = []
    if profile.soil_ph is not None:
        variables.append("soil_ph")
    if profile.soil_organic_carbon is not None:
        variables.append("soil_organic_carbon")
    if profile.soil_moisture is not None:
        variables.append("soil_moisture")
    if profile.rainfall_mm_year is not None or profile.rainfall_qualitative is not None:
        variables.append("rainfall")
    if profile.temperature_c is not None:
        variables.append("temperature")
    if profile.land_use_type:
        variables.append("land_use_type")
    if profile.biodiversity_indicators:
        variables.append("biodiversity_indicators")
    if profile.human_impact_indicators:
        variables.append("human_impact_indicators")
    return variables


def _edge_and_claim(db: Session, edge: KnowledgeEdge) -> tuple[ScientificClaim | None, ScientificSource | None, str | None]:
    if not edge.source_claim_id:
        return None, None, None
    claim = db.get(ScientificClaim, edge.source_claim_id)
    if claim is None:
        return None, None, None
    source = db.get(ScientificSource, claim.source_id) if claim.source_id else None
    excerpt = None
    if claim.evidence_chunk_id:
        chunk = db.get(EvidenceChunk, claim.evidence_chunk_id)
        excerpt = chunk.text if chunk else None
    return claim, source, excerpt


def _build_recommendation(
    db: Session,
    intervention: Intervention,
    profile: EnvironmentalProfile,
    graph,
    concern_keys: list[str],
) -> RecommendationBuild:
    direct_edges = [
        e for e in db.query(KnowledgeEdge).filter(KnowledgeEdge.source_node_id.isnot(None)).all()
        if e.source_node_id and _node_name(db, e.source_node_id) == intervention.id
    ]

    mechanisms: list[str] = []
    evidence_rows: list[dict[str, Any]] = []
    strengths: list[int] = []
    limitations_set: list[str] = []
    reasoning_steps: list[dict[str, Any]] = []
    impacted_metrics = list(intervention.target_metrics)

    ecosystem_mismatch = bool(
        intervention.ecosystem_context
        and profile.ecosystem_type
        and not any(
            profile.ecosystem_type.lower() in ctx.lower() or ctx.lower() in profile.ecosystem_type.lower()
            for ctx in intervention.ecosystem_context
        )
    )

    for edge in direct_edges:
        claim, source, excerpt = _edge_and_claim(db, edge)
        if edge.mechanism:
            mechanisms.append(edge.mechanism)
        strengths.append(_STRENGTH_RANK.get(edge.evidence_strength, 0))
        if edge.limitations and edge.limitations not in limitations_set:
            limitations_set.append(edge.limitations)
        reasoning_steps.append(
            {
                "from_node": intervention.id,
                "relation": edge.relation_type,
                "to_node": _node_name(db, edge.target_node_id),
                "evidence_strength": edge.evidence_strength,
                "source_claim_id": edge.source_claim_id,
            }
        )
        if claim is not None:
            verified = verify_claim(claim, source, excerpt, ecosystem_mismatch=ecosystem_mismatch)
            evidence_rows.append(verified.__dict__)

        # Extend one more hop downstream if it lands on a biodiversity indicator
        target_name = _node_name(db, edge.target_node_id)
        downstream_paths = find_paths(graph, target_name, "species_richness", max_hops=2)
        for path in downstream_paths[:1]:
            for step in path:
                reasoning_steps.append(
                    {
                        "from_node": step["from"],
                        "relation": step["relation"],
                        "to_node": step["to"],
                        "evidence_strength": step["evidence_strength"],
                        "source_claim_id": step.get("source_claim_id"),
                    }
                )
                if step["to"] not in impacted_metrics:
                    impacted_metrics.append(step["to"])

    avg_rank = round(sum(strengths) / len(strengths)) if strengths else 0
    avg_strength_label = _RANK_TO_STRENGTH.get(avg_rank, "hypothesis")

    constraint_result = check_constraints(intervention, profile)
    trade_offs = list(limitations_set)
    for unk in constraint_result.unknowns:
        trade_offs.append(f"Unknown factor: {unk}")
    if avg_strength_label in ("weak", "hypothesis"):
        trade_offs.append(
            "Evidence for this effect is currently weak or hypothesis-level (see evidence table); "
            "do not treat the expected benefit as guaranteed."
        )

    heuristic = compute_heuristic_score(intervention, avg_strength_label, constraint_result, profile)

    confidence_level = "low"
    if avg_strength_label == "strong" and not constraint_result.water_conflict and not ecosystem_mismatch:
        confidence_level = "high"
    elif avg_strength_label in ("strong", "moderate") and not constraint_result.water_conflict:
        confidence_level = "medium"
    confidence_reason = (
        f"Average supporting evidence strength is '{avg_strength_label}'"
        + (", but a water-availability conflict was detected" if constraint_result.water_conflict else "")
        + (", and the cited evidence's ecosystem context does not clearly match this profile" if ecosystem_mismatch else "")
        + "."
    )

    monitoring_plan = []
    for metric in impacted_metrics:
        has_baseline = (
            db.query(EnvironmentalObservation)
            .filter(EnvironmentalObservation.profile_id == profile.id, EnvironmentalObservation.metric == metric)
            .first()
            is not None
        )
        expected_direction = None
        for step in reasoning_steps:
            if step["to_node"] == metric:
                if step["relation"] in ("may_improve", "supports") and step["evidence_strength"] in ("strong", "moderate"):
                    expected_direction = "increase"
                elif step["relation"] == "may_reduce" and step["evidence_strength"] in ("strong", "moderate"):
                    expected_direction = "decrease"
        entry = generate_monitoring_entry(metric, intervention.typical_time_horizon or "medium", expected_direction, has_baseline)
        monitoring_plan.append(entry.__dict__)

    why_text = " ".join(mechanisms) if mechanisms else "Mechanism not established by a specific source in this corpus."

    return RecommendationBuild(
        intervention=intervention,
        title=intervention.name,
        what_to_do=intervention.description,
        why_it_may_work=why_text,
        impacted_metrics=impacted_metrics,
        time_horizon=intervention.typical_time_horizon or "medium",
        feasibility_constraints=constraint_result.feasibility_constraints,
        trade_offs=trade_offs,
        confidence_level=confidence_level,
        confidence_reason=confidence_reason,
        evidence=evidence_rows,
        heuristic_score=heuristic,
        monitoring_plan=monitoring_plan,
    )


_NODE_NAME_CACHE: dict[str, str] = {}


def _node_name(db: Session, node_id: str) -> str | None:
    if node_id in _NODE_NAME_CACHE:
        return _NODE_NAME_CACHE[node_id]
    from app.models.knowledge import KnowledgeNode

    node = db.get(KnowledgeNode, node_id)
    if node:
        _NODE_NAME_CACHE[node_id] = node.canonical_name
        return node.canonical_name
    return None


def run_assessment(
    db: Session,
    profile: EnvironmentalProfile,
    conversation_id: str | None = None,
    previous_assessment: Assessment | None = None,
) -> Assessment:
    known_facts = _known_facts(profile)
    variables = _variables_considered(profile)
    unknowns = [f for f in [
        "soil_ph" if profile.soil_ph is None else None,
        "soil_organic_carbon" if profile.soil_organic_carbon is None else None,
        "soil_moisture" if profile.soil_moisture is None else None,
        "rainfall" if (profile.rainfall_mm_year is None and profile.rainfall_qualitative is None) else None,
        "temperature" if profile.temperature_c is None else None,
        "biodiversity_indicators" if not profile.biodiversity_indicators else None,
        "human_impact_indicators" if not profile.human_impact_indicators else None,
    ] if f]

    version = 1
    if previous_assessment is not None:
        version = previous_assessment.version + 1

    if len(variables) < 3:
        assessment = Assessment(
            profile_id=profile.id,
            conversation_id=conversation_id,
            version=version,
            status="insufficient_data",
            assessment_summary=(
                f"Only {len(variables)} environmental variable(s) are currently known "
                f"({', '.join(variables) if variables else 'none'}). " + INSUFFICIENT_VARIABLES_MESSAGE
            ),
            known_facts=known_facts,
            unknowns=unknowns,
            variables_considered=variables,
            reasoning_paths=[],
            overall_limitations=[INSUFFICIENT_VARIABLES_MESSAGE],
            previous_assessment_id=previous_assessment.id if previous_assessment else None,
        )
        db.add(assessment)
        db.flush()
        return assessment

    concerns = detect_concerns(profile)
    candidate_ids: list[str] = []
    for concern in concerns:
        for iid in CONCERN_TO_INTERVENTIONS.get(concern.key, []):
            if iid not in candidate_ids:
                candidate_ids.append(iid)
    candidate_ids = candidate_ids[:5]

    graph = build_graph(db)
    _NODE_NAME_CACHE.clear()

    recommendations_built: list[RecommendationBuild] = []
    reasoning_paths_out: list[dict[str, Any]] = []
    for iid in candidate_ids:
        intervention = db.get(Intervention, iid)
        if intervention is None:
            continue
        concern_keys_for_this = [c.key for c in concerns if iid in CONCERN_TO_INTERVENTIONS.get(c.key, [])]
        built = _build_recommendation(db, intervention, profile, graph, concern_keys_for_this)
        recommendations_built.append(built)

        involved_vars = [CONCERN_TO_NODE.get(k, k) for k in concern_keys_for_this]
        steps = []
        for edge in db.query(KnowledgeEdge).all():
            src_name = _node_name(db, edge.source_node_id)
            if src_name == intervention.id:
                steps.append({
                    "from_node": src_name,
                    "relation": edge.relation_type,
                    "to_node": _node_name(db, edge.target_node_id),
                    "evidence_strength": edge.evidence_strength,
                    "source_claim_id": edge.source_claim_id,
                })
        reasoning_paths_out.append({
            "variables": involved_vars + [intervention.id],
            "steps": steps,
            "narrative": (
                f"Detected concern(s) [{', '.join(concern_keys_for_this)}] relate to candidate intervention "
                f"'{intervention.name}', which is linked in the knowledge graph to: "
                f"{', '.join(s['to_node'] for s in steps if s['to_node'])}."
            ),
        })

    concern_summary = "; ".join(c.explanation for c in concerns) if concerns else "No acute concern thresholds were triggered by the currently known variables."
    assessment_summary = (
        f"Profile '{profile.name}'" + (f" in {profile.region}" if profile.region else "")
        + (f" ({profile.ecosystem_type})" if profile.ecosystem_type else "") + ". "
        f"Considered {len(variables)} known variable(s): {', '.join(variables)}. {concern_summary}"
    )

    overall_limitations = [
        "This assessment reflects only the environmental variables currently provided; unmeasured factors "
        "(e.g. local species composition, exact water budget) could change which intervention is most suitable.",
    ]
    if not concerns:
        overall_limitations.append(
            "No candidate interventions were generated because no concern thresholds were triggered by the "
            "current profile data; provide a biodiversity trend observation or additional metrics to refine this."
        )

    diff = []
    if previous_assessment is not None:
        diff = _compute_diff(previous_assessment, known_facts, recommendations_built)

    assessment = Assessment(
        profile_id=profile.id,
        conversation_id=conversation_id,
        version=version,
        status="completed",
        assessment_summary=assessment_summary,
        known_facts=known_facts,
        unknowns=unknowns,
        variables_considered=variables,
        reasoning_paths=reasoning_paths_out,
        overall_limitations=overall_limitations,
        previous_assessment_id=previous_assessment.id if previous_assessment else None,
        diff_from_previous=diff,
    )
    db.add(assessment)
    db.flush()

    for built in recommendations_built:
        rec = Recommendation(
            assessment_id=assessment.id,
            profile_id=profile.id,
            intervention_id=built.intervention.id,
            title=built.title,
            what_to_do=built.what_to_do,
            why_it_may_work=built.why_it_may_work,
            impacted_metrics=built.impacted_metrics,
            time_horizon=built.time_horizon,
            feasibility_constraints=built.feasibility_constraints,
            trade_offs=built.trade_offs,
            confidence_level=built.confidence_level,
            confidence_reason=built.confidence_reason,
            evidence=built.evidence,
            heuristic_score=built.heuristic_score,
        )
        db.add(rec)
        db.flush()

        from app.models.monitoring import MonitoringPlan

        for m in built.monitoring_plan:
            db.add(MonitoringPlan(recommendation_id=rec.id, **m))

    db.commit()
    db.refresh(assessment)
    return assessment


def _compute_diff(
    previous: Assessment, new_known_facts: list[dict[str, Any]], new_recommendations: list[RecommendationBuild]
) -> list[dict[str, Any]]:
    diff: list[dict[str, Any]] = []
    prev_by_field = {f["field"]: f["value"] for f in previous.known_facts}
    new_by_field = {f["field"]: f["value"] for f in new_known_facts}
    for field_name, new_value in new_by_field.items():
        old_value = prev_by_field.get(field_name)
        if old_value != new_value:
            diff.append({"type": "field_changed", "field": field_name, "previous_value": old_value, "current_value": new_value})

    prev_titles = {r.title for r in previous.recommendations}
    new_titles = {b.title for b in new_recommendations}
    for added in new_titles - prev_titles:
        diff.append({"type": "recommendation_added", "title": added})
    for removed in prev_titles - new_titles:
        diff.append({"type": "recommendation_removed", "title": removed})
    return diff
