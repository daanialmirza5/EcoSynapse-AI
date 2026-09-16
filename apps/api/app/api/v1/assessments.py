from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.v1.serializers import serialize_assessment
from app.db.session import get_db
from app.models.profile import EnvironmentalProfile
from app.models.recommendation import Assessment
from app.reasoning.engine import run_assessment
from app.schemas.assessment import AssessmentCreate, AssessmentOut

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("", response_model=AssessmentOut, status_code=201)
def create_assessment(payload: AssessmentCreate, db: Session = Depends(get_db)):
    profile = db.get(EnvironmentalProfile, payload.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    assessment = run_assessment(db, profile, conversation_id=payload.conversation_id)
    return serialize_assessment(assessment)


@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return serialize_assessment(assessment)


@router.post("/{assessment_id}/reassess", response_model=AssessmentOut, status_code=201)
def reassess(assessment_id: str, db: Session = Depends(get_db)):
    previous = db.get(Assessment, assessment_id)
    if previous is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    profile = db.get(EnvironmentalProfile, previous.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    new_assessment = run_assessment(db, profile, conversation_id=previous.conversation_id, previous_assessment=previous)
    return serialize_assessment(new_assessment)


@router.get("/{assessment_id}/export")
def export_assessment(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    payload = serialize_assessment(assessment).model_dump(mode="json")
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="assessment-{assessment_id}.json"'},
    )
