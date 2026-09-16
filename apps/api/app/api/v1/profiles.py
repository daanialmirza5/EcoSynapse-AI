from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.conversations.clarify import missing_fields, profile_completeness
from app.db.session import get_db
from app.models.profile import EnvironmentalObservation, EnvironmentalProfile
from app.schemas.profile import (
    EnvironmentalProfileCreate,
    EnvironmentalProfileOut,
    EnvironmentalProfileUpdate,
    ObservationCreate,
    ObservationOut,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _sync_missing_fields(profile: EnvironmentalProfile) -> None:
    profile.missing_fields = missing_fields(profile)
    profile.uncertainty_metadata = {
        **(profile.uncertainty_metadata or {}),
        "completeness": profile_completeness(profile),
    }


@router.post("", response_model=EnvironmentalProfileOut, status_code=201)
def create_profile(payload: EnvironmentalProfileCreate, db: Session = Depends(get_db)):
    profile = EnvironmentalProfile(**payload.model_dump())
    _sync_missing_fields(profile)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/{profile_id}", response_model=EnvironmentalProfileOut)
def get_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = db.get(EnvironmentalProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/{profile_id}", response_model=EnvironmentalProfileOut)
def update_profile(profile_id: str, payload: EnvironmentalProfileUpdate, db: Session = Depends(get_db)):
    profile = db.get(EnvironmentalProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    _sync_missing_fields(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/{profile_id}/observations", response_model=ObservationOut, status_code=201)
def add_observation(profile_id: str, payload: ObservationCreate, db: Session = Depends(get_db)):
    profile = db.get(EnvironmentalProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    observation = EnvironmentalObservation(profile_id=profile_id, **payload.model_dump())
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation


@router.get("/{profile_id}/observations", response_model=list[ObservationOut])
def list_observations_endpoint(profile_id: str, db: Session = Depends(get_db)):
    profile = db.get(EnvironmentalProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return (
        db.query(EnvironmentalObservation)
        .filter(EnvironmentalObservation.profile_id == profile_id)
        .order_by(EnvironmentalObservation.id)
        .all()
    )
