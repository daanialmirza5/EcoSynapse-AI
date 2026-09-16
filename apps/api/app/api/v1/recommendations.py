from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.serializers import serialize_recommendation
from app.db.session import get_db
from app.models.recommendation import Recommendation
from app.schemas.assessment import EvidenceRef, MonitoringPlanItem, RecommendationOut

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{recommendation_id}", response_model=RecommendationOut)
def get_recommendation(recommendation_id: str, db: Session = Depends(get_db)):
    rec = db.get(Recommendation, recommendation_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return serialize_recommendation(rec)


@router.get("/{recommendation_id}/evidence", response_model=list[EvidenceRef])
def get_recommendation_evidence(recommendation_id: str, db: Session = Depends(get_db)):
    rec = db.get(Recommendation, recommendation_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return serialize_recommendation(rec).evidence


@router.get("/{recommendation_id}/monitoring", response_model=list[MonitoringPlanItem])
def get_recommendation_monitoring(recommendation_id: str, db: Session = Depends(get_db)):
    rec = db.get(Recommendation, recommendation_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return serialize_recommendation(rec).monitoring_plan
