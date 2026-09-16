from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import EvidenceStatus


class ScientificSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    authors: list[str]
    organization: str | None
    publication_year: int | None
    doi: str | None
    url: str | None
    source_type: str
    abstract: str | None
    full_text_available: bool
    is_verified: bool
    ecosystem_context: list[str]
    limitations: str | None


class EvidenceChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    source_id: str
    text: str
    section: str | None


class RetrievedEvidenceItem(BaseModel):
    chunk_id: str
    source: ScientificSourceOut
    excerpt: str
    relevance_score: float
    match_reasons: list[str]


class RetrievalInspectRequest(BaseModel):
    query: str
    profile_id: str | None = None
    top_k: int = 6


class RetrievalTrace(BaseModel):
    query: str
    expanded_terms: list[str]
    graph_concepts: list[str]
    semantic_candidates: int
    lexical_candidates: int
    merged_candidates: int
    results: list[RetrievedEvidenceItem]


class EvidenceTableRow(BaseModel):
    claim: str
    claim_type: str
    source_id: str | None
    source_title: str | None
    citation: str | None
    excerpt: str | None
    applicability: str
    limitations: str | None
    evidence_status: EvidenceStatus
    created_at: datetime | None = None
