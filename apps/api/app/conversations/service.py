"""Conversation turn orchestration: extract -> merge into profile -> detect
conflicts -> generate clarifying questions -> compose assistant reply.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.ai.llm import get_llm_provider
from app.conversations.clarify import (
    generate_clarifying_questions,
    profile_completeness,
    ready_for_assessment,
)
from app.conversations.extraction import extract_from_text
from app.models.conversation import Conversation, Message
from app.models.profile import EnvironmentalProfile
from app.schemas.common import MessageRole

_PROFILE_SCALAR_FIELDS = {
    "soil_ph", "soil_organic_carbon", "soil_moisture", "rainfall_mm_year",
    "rainfall_qualitative", "temperature_c", "ecosystem_type", "land_use_type",
}


def get_or_create_profile_for_conversation(db: Session, conversation: Conversation) -> EnvironmentalProfile:
    profile = (
        db.query(EnvironmentalProfile)
        .filter(EnvironmentalProfile.conversation_id == conversation.id)
        .order_by(EnvironmentalProfile.created_at.desc())
        .first()
    )
    if profile is None:
        profile = EnvironmentalProfile(conversation_id=conversation.id, name=f"Profile for {conversation.title}")
        db.add(profile)
        db.flush()
    return profile


def apply_extraction_to_profile(
    profile: EnvironmentalProfile, extraction_fields: dict[str, Any]
) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    for key, new_value in extraction_fields.items():
        if key not in _PROFILE_SCALAR_FIELDS:
            continue
        current = getattr(profile, key, None)
        if current is not None and current != new_value:
            conflicts.append({"field": key, "previous_value": current, "new_value": new_value})
        setattr(profile, key, new_value)
    return conflicts


def apply_structured_input(profile: EnvironmentalProfile, structured: dict[str, Any]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    for key, new_value in structured.items():
        if not hasattr(profile, key) or new_value is None:
            continue
        if key in ("biodiversity_indicators", "human_impact_indicators") and isinstance(new_value, dict):
            merged = dict(getattr(profile, key) or {})
            merged.update(new_value)
            setattr(profile, key, merged)
            continue
        if key == "constraints" and isinstance(new_value, list):
            merged_list = list(dict.fromkeys((profile.constraints or []) + new_value))
            profile.constraints = merged_list
            continue
        current = getattr(profile, key, None)
        if key in _PROFILE_SCALAR_FIELDS and current is not None and current != new_value:
            conflicts.append({"field": key, "previous_value": current, "new_value": new_value})
        setattr(profile, key, new_value)
    return conflicts


def compose_assistant_reply(
    extraction_fields: dict[str, Any],
    biodiversity_indicators: dict[str, Any],
    human_impact_indicators: dict[str, Any],
    clarifying_questions: list,
    ready: bool,
    completeness: float,
) -> str:
    lines: list[str] = []
    captured = list(extraction_fields.keys()) + list(biodiversity_indicators.keys()) + list(human_impact_indicators.keys())
    if captured:
        readable = ", ".join(f.replace("_", " ") for f in captured)
        lines.append(f"Noted: {readable}.")
    else:
        lines.append("I didn't detect any new structured environmental values in that message.")

    lines.append(f"Current profile completeness: {int(completeness * 100)}%.")

    if clarifying_questions:
        lines.append("To sharpen the assessment, could you tell me:")
        for q in clarifying_questions:
            lines.append(f"- {q.question}")
    if ready:
        lines.append(
            "There is enough information to run an initial assessment now, or you can keep adding detail first."
        )
    else:
        lines.append("A few more details will let the reasoning engine consider at least three variables together.")

    text = "\n".join(lines)
    llm = get_llm_provider()
    return llm.complete(
        system_prompt=(
            "You are rephrasing an already-correct assistant message for tone only. "
            "Do not add, remove, or change any factual content, numbers, or questions."
        ),
        user_prompt=text,
    )


def handle_user_turn(
    db: Session,
    conversation: Conversation,
    content: str,
    structured_input: dict[str, Any] | None,
) -> dict[str, Any]:
    user_message = Message(conversation_id=conversation.id, role=MessageRole.USER.value, content=content)
    db.add(user_message)

    profile = get_or_create_profile_for_conversation(db, conversation)

    extraction = extract_from_text(content)
    conflicts = apply_extraction_to_profile(profile, extraction.fields)
    if extraction.biodiversity_indicators:
        profile.biodiversity_indicators = {**profile.biodiversity_indicators, **extraction.biodiversity_indicators}
    if extraction.human_impact_indicators:
        profile.human_impact_indicators = {**profile.human_impact_indicators, **extraction.human_impact_indicators}
    if extraction.constraints:
        profile.constraints = list(dict.fromkeys((profile.constraints or []) + extraction.constraints))

    if structured_input:
        conflicts += apply_structured_input(profile, structured_input)

    profile.missing_fields = _compute_missing(profile)
    if conflicts:
        profile.uncertainty_metadata = {
            **(profile.uncertainty_metadata or {}),
            "recent_conflicts": conflicts,
        }

    completeness = profile_completeness(profile)
    clarifying = generate_clarifying_questions(profile)
    ready = ready_for_assessment(profile)

    reply_text = compose_assistant_reply(
        extraction.fields, extraction.biodiversity_indicators, extraction.human_impact_indicators,
        clarifying, ready, completeness,
    )

    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT.value,
        content=reply_text,
        structured_metadata={
            "extracted_fields": extraction.fields,
            "clarifying_questions": [q.__dict__ for q in clarifying],
            "conflicts": conflicts,
            "profile_completeness": completeness,
            "ready_for_assessment": ready,
        },
    )
    db.add(assistant_message)
    db.flush()

    return {
        "assistant_message": assistant_message,
        "profile": profile,
        "clarifying_questions": clarifying,
        "profile_completeness": completeness,
        "extracted_fields": extraction.fields,
        "conflicts": conflicts,
        "ready_for_assessment": ready,
    }


def _compute_missing(profile: EnvironmentalProfile) -> list[str]:
    from app.conversations.clarify import missing_fields

    return missing_fields(profile)
