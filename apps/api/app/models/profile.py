from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import JSON, Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EnvironmentalProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A structured snapshot of a piece of land under investigation.

    Every numeric field is optional: the reasoning engine must work with
    partial information and explicitly track what is unknown rather than
    guessing values.
    """

    __tablename__ = "environmental_profiles"

    conversation_id: Mapped[str | None] = mapped_column(ForeignKey("conversations.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), default="Untitled land profile")
    region: Mapped[str | None] = mapped_column(String(200), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    ecosystem_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    land_use_type: Mapped[str | None] = mapped_column(String(120), nullable=True)

    soil_ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    soil_organic_carbon: Mapped[float | None] = mapped_column(Float, nullable=True)  # percent
    soil_moisture: Mapped[float | None] = mapped_column(Float, nullable=True)  # percent volumetric, if known

    rainfall_mm_year: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_qualitative: Mapped[str | None] = mapped_column(String(20), nullable=True)  # low|medium|high
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)

    biodiversity_indicators: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    human_impact_indicators: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    constraints: Mapped[list[str]] = mapped_column(JSON, default=list)

    data_source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unit_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    missing_fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    uncertainty_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    observations: Mapped[list["EnvironmentalObservation"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class EnvironmentalObservation(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "environmental_observations"

    profile_id: Mapped[str] = mapped_column(ForeignKey("environmental_profiles.id"), nullable=False)
    metric: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    observation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(String(40), default="user_reported")  # user_reported|sensor|estimate
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)  # low|medium|high
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    profile: Mapped[EnvironmentalProfile] = relationship(back_populates="observations")
