from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin


class MonitoringPlan(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "monitoring_plans"

    recommendation_id: Mapped[str] = mapped_column(ForeignKey("recommendations.id"), nullable=False)
    metric: Mapped[str] = mapped_column(String(80), nullable=False)
    baseline_requirement: Mapped[str] = mapped_column(Text, nullable=False)
    target: Mapped[str | None] = mapped_column(Text, nullable=True)
    measurement_method: Mapped[str] = mapped_column(Text, nullable=False)
    # Free-form generated sentences, not a controlled vocabulary -- Text
    # rather than a bounded VARCHAR. A bounded String(40) here previously
    # caused a Postgres-only StringDataRightTruncation error for longer unit
    # descriptions (e.g. "structural/habitat diversity index
    # (method-dependent)"), invisible under SQLite because SQLite does not
    # enforce declared VARCHAR length limits at all.
    measurement_frequency: Mapped[str] = mapped_column(Text, nullable=False)
    time_horizon: Mapped[str] = mapped_column(String(20), default="medium")
    unit: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_direction: Mapped[str | None] = mapped_column(String(20), nullable=True)  # increase|decrease|stabilize
    success_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    uncertainty: Mapped[str | None] = mapped_column(Text, nullable=True)

    recommendation = relationship("Recommendation", back_populates="monitoring_plan")
