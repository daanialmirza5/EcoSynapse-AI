from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.profile import EnvironmentalObservation, EnvironmentalProfile


def get_profile_or_404(db: Session, profile_id: str) -> EnvironmentalProfile | None:
    return db.get(EnvironmentalProfile, profile_id)


def list_observations(db: Session, profile_id: str) -> list[EnvironmentalObservation]:
    return (
        db.query(EnvironmentalObservation)
        .filter(EnvironmentalObservation.profile_id == profile_id)
        .order_by(EnvironmentalObservation.observation_date.desc().nullslast())
        .all()
    )
