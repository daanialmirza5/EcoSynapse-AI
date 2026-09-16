from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import assessments, conversations, knowledge, profiles, recommendations

api_router = APIRouter()
api_router.include_router(conversations.router)
api_router.include_router(profiles.router)
api_router.include_router(assessments.router)
api_router.include_router(knowledge.router)
api_router.include_router(recommendations.router)
