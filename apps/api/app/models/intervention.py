from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Intervention(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A candidate ecological intervention in the catalog.

    This is a static catalog entry (the "what could be done"). Whether it is
    *suitable* for a given profile is decided at reasoning time by the
    constraint engine, not baked in here.
    """

    __tablename__ = "interventions"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_metrics: Mapped[list[str]] = mapped_column(JSON, default=list)
    prerequisites: Mapped[list[str]] = mapped_column(JSON, default=list)
    constraints: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    ecosystem_context: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_claim_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    water_sensitivity: Mapped[str | None] = mapped_column(String(20), nullable=True)  # low|medium|high
    typical_time_horizon: Mapped[str | None] = mapped_column(String(20), nullable=True)
