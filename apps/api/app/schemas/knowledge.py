from __future__ import annotations

from pydantic import BaseModel


class KnowledgeNodeOut(BaseModel):
    id: str
    node_type: str
    canonical_name: str
    description: str | None


class KnowledgeEdgeOut(BaseModel):
    id: str
    source_node_id: str
    target_node_id: str
    relation_type: str
    mechanism: str | None
    evidence_strength: str
    limitations: str | None
    source_claim_id: str | None


class KnowledgeGraphOut(BaseModel):
    nodes: list[KnowledgeNodeOut]
    edges: list[KnowledgeEdgeOut]


class GraphPathStep(BaseModel):
    node: KnowledgeNodeOut
    edge_in: KnowledgeEdgeOut | None = None


class GraphPath(BaseModel):
    steps: list[GraphPathStep]
    overall_evidence_strength: str
