from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.conversations.service import handle_user_turn
from app.db.session import get_db
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    ClarifyingQuestion,
    ConversationCreate,
    ConversationOut,
    ConversationTurnResponse,
    MessageCreate,
    MessageOut,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationOut, status_code=201)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    conversation = Conversation(title=payload.title or "New assessment", session_id=payload.session_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db), limit: int = 50, offset: int = 0):
    return (
        db.query(Conversation)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(min(limit, 200))
        .all()
    )


@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(conversation_id: str, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )


@router.post("/{conversation_id}/messages", response_model=ConversationTurnResponse)
def post_message(conversation_id: str, payload: MessageCreate, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = handle_user_turn(db, conversation, payload.content, payload.structured_input)
    db.commit()
    db.refresh(result["assistant_message"])
    db.refresh(result["profile"])

    return ConversationTurnResponse(
        conversation_id=conversation.id,
        profile_id=result["profile"].id,
        assistant_message=result["assistant_message"],
        clarifying_questions=[ClarifyingQuestion(**q.__dict__) for q in result["clarifying_questions"]],
        profile_completeness=result["profile_completeness"],
        extracted_fields=result["extracted_fields"],
        conflicts=result["conflicts"],
        ready_for_assessment=result["ready_for_assessment"],
    )


@router.get("/{conversation_id}/export")
def export_conversation(conversation_id: str, format: str = "json", db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    if format.lower() == "markdown":
        md_lines = [
            f"# Conversation Export: {conversation.title}",
            f"**Session ID:** `{conversation.session_id or 'N/A'}`",
            f"**Created At:** {conversation.created_at}",
            "",
            "---",
            "",
        ]
        for msg in messages:
            sender = msg.role.capitalize()
            md_lines.append(f"### {sender} ({msg.created_at})")
            md_lines.append(f"{msg.content}\n")
        return {"format": "markdown", "content": "\n".join(md_lines)}

    return {
        "format": "json",
        "conversation": {
            "id": conversation.id,
            "title": conversation.title,
            "session_id": conversation.session_id,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
        },
    }
