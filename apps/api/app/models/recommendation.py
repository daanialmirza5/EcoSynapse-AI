from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.monitoring import MonitoringPlan


class Assessment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One run of the reasoning pipeline over a profile (a 'version' of the
    assessment). A profile can be reassessed multiple times as data changes.
    """

    __tablename__ = "assessments"

    profile_id: Mapped[str] = mapped_column(ForeignKey("environmental_profiles.id"), nullable=False)
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey("conversations.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="completed")

    assessment_summary: Mapped[str] = mapped_column(Text, default="")
    known_facts: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    unknowns: Mapped[list[str]] = mapped_column(JSON, default=list)
    variables_considered: Mapped[list[str]] = mapped_column(JSON, default=list)
    reasoning_paths: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    overall_limitations: Mapped[list[str]] = mapped_column(JSON, default=list)
    previous_assessment_id: Mapped[str | None] = mapped_column(ForeignKey("assessments.id"), nullable=True)
    diff_from_previous: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class Recommendation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "recommendations"

    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), nullable=False)
    profile_id: Mapped[str] = mapped_column(ForeignKey("environmental_profiles.id"), nullable=False)
    intervention_id: Mapped[str | None] = mapped_column(ForeignKey("interventions.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    what_to_do: Mapped[str] = mapped_column(Text, nullable=False)
    why_it_may_work: Mapped[str] = mapped_column(Text, nullable=False)
    impacted_metrics: Mapped[list[str]] = mapped_column(JSON, default=list)
    time_horizon: Mapped[str] = mapped_column(String(20), default="medium")  # short|medium|long
    feasibility_constraints: Mapped[list[str]] = mapped_column(JSON, default=list)
    trade_offs: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence_level: Mapped[str] = mapped_column(String(20), default="low")  # low|medium|high
    confidence_reason: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    heuristic_score: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="proposed")

    assessment: Mapped[Assessment] = relationship(back_populates="recommendations")
    monitoring_plan: Mapped[list["MonitoringPlan"]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan"
    )
