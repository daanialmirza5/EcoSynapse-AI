from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ScientificSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A traceable scientific or institutional source.

    ``source_type`` of ``sample_illustrative`` marks records that are NOT
    verified real publications — used only when real evidence could not be
    sourced for a demo scenario. See docs/scientific-grounding.md.
    """

    __tablename__ = "scientific_sources"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    authors: Mapped[list[str]] = mapped_column(JSON, default=list)
    organization: Mapped[str | None] = mapped_column(String(300), nullable=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doi: Mapped[str | None] = mapped_column(String(200), nullable=True)
    url: Mapped[str | None] = mapped_column(String(600), nullable=True)
    source_type: Mapped[str] = mapped_column(String(40), default="peer_reviewed_article")
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_text_available: Mapped[bool] = mapped_column(Boolean, default=False)
    license_notes: Mapped[str | None] = mapped_column(String(400), nullable=True)
    ingestion_status: Mapped[str] = mapped_column(String(30), default="ingested")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    ecosystem_context: Mapped[list[str]] = mapped_column(JSON, default=list)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)

    chunks: Mapped[list["EvidenceChunk"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class EvidenceChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evidence_chunks"

    source_id: Mapped[str] = mapped_column(ForeignKey("scientific_sources.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    section: Mapped[str | None] = mapped_column(String(200), nullable=True)
    embedding: Mapped[list[float]] = mapped_column(JSON, default=list)
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    extraction_status: Mapped[str] = mapped_column(String(30), default="ok")

    source: Mapped[ScientificSource] = relationship(back_populates="chunks")


class ScientificClaim(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A discrete, checkable statement extracted from (or grounded in) evidence.

    ``claim_type`` must be one of the five categories mandated by the
    scientific-integrity policy: source_supported, model_derived, hypothesis,
    user_observation, unknown.
    """

    __tablename__ = "scientific_claims"

    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(30), nullable=False)
    evidence_strength: Mapped[str] = mapped_column(String(20), default="moderate")  # weak|moderate|strong
    source_id: Mapped[str | None] = mapped_column(ForeignKey("scientific_sources.id"), nullable=True)
    evidence_chunk_id: Mapped[str | None] = mapped_column(ForeignKey("evidence_chunks.id"), nullable=True)
    conditions: Mapped[list[str]] = mapped_column(JSON, default=list)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(30), default="unverified")

    source: Mapped[ScientificSource | None] = relationship()
