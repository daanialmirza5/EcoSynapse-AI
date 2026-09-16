from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import MessageRole


class ConversationCreate(BaseModel):
    title: str | None = None
    session_id: str | None = None


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    structured_input: dict[str, Any] | None = Field(
        default=None, description="Optional structured JSON profile data provided alongside text."
    )


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    structured_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ClarifyingQuestion(BaseModel):
    field: str
    question: str
    reason: str
    priority: int


class ConversationTurnResponse(BaseModel):
    conversation_id: str
    profile_id: str
    assistant_message: MessageOut
    clarifying_questions: list[ClarifyingQuestion]
    profile_completeness: float
    extracted_fields: dict[str, Any]
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    ready_for_assessment: bool
