from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeNode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "knowledge_nodes"

    node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    node_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class KnowledgeEdge(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "knowledge_edges"

    source_node_id: Mapped[str] = mapped_column(ForeignKey("knowledge_nodes.id"), nullable=False)
    target_node_id: Mapped[str] = mapped_column(ForeignKey("knowledge_nodes.id"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    mechanism: Mapped[str | None] = mapped_column(Text, nullable=True)
    conditions: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_claim_id: Mapped[str | None] = mapped_column(ForeignKey("scientific_claims.id"), nullable=True)
    evidence_strength: Mapped[str] = mapped_column(String(20), default="hypothesis")
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_node: Mapped[KnowledgeNode] = relationship(foreign_keys=[source_node_id])
    target_node: Mapped[KnowledgeNode] = relationship(foreign_keys=[target_node_id])
