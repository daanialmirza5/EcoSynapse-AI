from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.knowledge.ingestion import ingest_source
from app.models.evidence import ScientificSource
from app.models.knowledge import KnowledgeEdge, KnowledgeNode
from app.models.profile import EnvironmentalProfile
from app.retrieval.hybrid import retrieve_with_trace
from app.schemas.evidence import (
    RetrievalInspectRequest,
    RetrievalTrace,
    RetrievedEvidenceItem,
    ScientificSourceOut,
)
from app.schemas.knowledge import KnowledgeEdgeOut, KnowledgeGraphOut, KnowledgeNodeOut

router = APIRouter(tags=["knowledge"])


class IngestRequest(BaseModel):
    title: str
    text: str | None = None
    authors: list[str] = Field(default_factory=list)
    organization: str | None = None
    publication_year: int | None = None
    doi: str | None = None
    url: str | None = None
    source_type: str = "user_uploaded"
    abstract: str | None = None
    ecosystem_context: list[str] = Field(default_factory=list)
    limitations: str | None = None
    is_verified: bool = False


class IngestResponse(BaseModel):
    source_id: str
    chunk_count: int
    warnings: list[str]


@router.post("/knowledge/ingest", response_model=IngestResponse, status_code=201)
def ingest(payload: IngestRequest, db: Session = Depends(get_db)):
    if payload.text and len(payload.text) > 500_000:
        raise HTTPException(status_code=413, detail="Document text too large (limit 500,000 characters)")
    result = ingest_source(db, **payload.model_dump())
    db.commit()
    return IngestResponse(source_id=result.source_id, chunk_count=len(result.chunk_ids), warnings=result.warnings)


@router.get("/knowledge/sources", response_model=list[ScientificSourceOut])
def list_sources(db: Session = Depends(get_db), limit: int = 100, offset: int = 0):
    return db.query(ScientificSource).offset(offset).limit(min(limit, 200)).all()


@router.get("/knowledge/sources/{source_id}", response_model=ScientificSourceOut)
def get_source(source_id: str, db: Session = Depends(get_db)):
    source = db.get(ScientificSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.get("/knowledge/graph", response_model=KnowledgeGraphOut)
def get_knowledge_graph(db: Session = Depends(get_db)):
    nodes = db.query(KnowledgeNode).all()
    edges = db.query(KnowledgeEdge).all()
    return KnowledgeGraphOut(
        nodes=[
            KnowledgeNodeOut(id=n.id, node_type=n.node_type, canonical_name=n.canonical_name, description=n.description)
            for n in nodes
        ],
        edges=[
            KnowledgeEdgeOut(
                id=e.id,
                source_node_id=e.source_node_id,
                target_node_id=e.target_node_id,
                relation_type=e.relation_type,
                mechanism=e.mechanism,
                evidence_strength=e.evidence_strength,
                limitations=e.limitations,
                source_claim_id=e.source_claim_id,
            )
            for e in edges
        ],
    )


@router.post("/retrieval/inspect", response_model=RetrievalTrace)
def inspect_retrieval(payload: RetrievalInspectRequest, db: Session = Depends(get_db)):
    profile = None
    if payload.profile_id:
        profile = db.get(EnvironmentalProfile, payload.profile_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

    trace = retrieve_with_trace(db, payload.query, profile=profile, top_k=payload.top_k)
    return RetrievalTrace(
        query=trace.query,
        expanded_terms=trace.expanded_terms,
        graph_concepts=trace.graph_concepts,
        semantic_candidates=trace.semantic_candidates,
        lexical_candidates=trace.lexical_candidates,
        merged_candidates=trace.merged_candidates,
        results=[
            RetrievedEvidenceItem(
                chunk_id=r.chunk_id,
                source=ScientificSourceOut.model_validate(r.source),
                excerpt=r.excerpt,
                relevance_score=r.relevance_score,
                semantic_score=r.semantic_score,
                lexical_score=r.lexical_score,
                matched_graph_concepts=r.matched_graph_concepts,
                match_reasons=r.match_reasons,
            )
            for r in trace.results
        ],
    )
