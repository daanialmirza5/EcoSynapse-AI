"""Loads the curated demo knowledge corpus (data/seed/*.json) into the database.

Idempotent: if sources already exist, seeding is skipped unless ``force=True``.
This is the only place the app creates ScientificSource/Claim/Node/Edge rows
in bulk from static files — everything else goes through the ingestion API.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.ai.embeddings import get_embedding_provider
from app.core.config import get_settings
from app.models.evidence import EvidenceChunk, ScientificClaim, ScientificSource
from app.models.intervention import Intervention
from app.models.knowledge import KnowledgeEdge, KnowledgeNode

logger = logging.getLogger(__name__)


def _data_dir() -> Path:
    """Locates data/seed/.

    Deployment layouts differ in how many directory levels separate this
    file from the repo's data/ folder (a plain monorepo checkout vs. a
    Docker image with its own COPY layout), so a fixed number of
    ``.parents[N]`` hops is fragile -- it previously broke silently inside
    Docker (IndexError, caught and swallowed by the startup lifespan's
    generic except, resulting in an app that boots with an EMPTY knowledge
    base and no visible error). ``SEED_DATA_DIR`` lets a deployment say
    explicitly where it put the data; the monorepo-relative guess remains
    the default for local/dev checkouts.
    """
    configured = get_settings().seed_data_dir
    if configured:
        return Path(configured)
    # apps/api/app/knowledge/seed.py -> repo_root/data/seed
    return Path(__file__).resolve().parents[4] / "data" / "seed"


def _load_json(name: str) -> list[dict]:
    path = _data_dir() / name
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def seed_all(db: Session, force: bool = False) -> dict[str, int]:
    existing = db.query(ScientificSource).count()
    if existing and not force:
        logger.info("Seed skipped: %d sources already present", existing)
        return {"sources": existing, "skipped": True}

    provider = get_embedding_provider()
    counts = {"sources": 0, "chunks": 0, "claims": 0, "nodes": 0, "edges": 0, "interventions": 0}

    # 1. Sources
    source_id_map: dict[str, str] = {}
    for row in _load_json("sources.json"):
        source = ScientificSource(
            title=row["title"],
            authors=row.get("authors", []),
            organization=row.get("organization"),
            publication_year=row.get("publication_year"),
            doi=row.get("doi"),
            url=row.get("url"),
            source_type=row.get("source_type", "peer_reviewed_article"),
            abstract=row.get("abstract"),
            full_text_available=False,
            ecosystem_context=row.get("ecosystem_context", []),
            limitations=row.get("limitations"),
            license_notes=row.get("license_notes"),
            is_verified=row.get("is_verified", True),
            ingestion_status="ingested",
        )
        db.add(source)
        db.flush()
        source_id_map[row["id"]] = source.id
        counts["sources"] += 1

        if source.abstract:
            chunk = EvidenceChunk(
                source_id=source.id,
                text=source.abstract,
                section="abstract",
                embedding=provider.embed(source.abstract),
            )
            db.add(chunk)
            counts["chunks"] += 1

    # 2. Nodes + Claims + Edges from relationships.json
    node_id_map: dict[str, str] = {}

    def get_or_create_node(name: str, node_type: str) -> str:
        if name in node_id_map:
            return node_id_map[name]
        node = KnowledgeNode(node_type=node_type, canonical_name=name, description=None)
        db.add(node)
        db.flush()
        node_id_map[name] = node.id
        counts["nodes"] += 1
        return node.id

    claim_id_map: dict[str, str] = {}
    for rel in _load_json("relationships.json"):
        from_id = get_or_create_node(rel["from_node"], rel["from_type"])
        to_id = get_or_create_node(rel["to_node"], rel["to_type"])

        db_source_id = source_id_map.get(rel["source_id"]) if rel.get("source_id") else None
        claim = ScientificClaim(
            claim_text=rel["claim_text"],
            claim_type=rel["claim_type"],
            evidence_strength=rel["evidence_strength"],
            source_id=db_source_id,
            conditions=rel.get("conditions", []),
            limitations=rel.get("limitations"),
            verification_status="verified" if rel["claim_type"] == "source_supported" else f"labeled_{rel['claim_type']}",
        )
        db.add(claim)
        db.flush()
        counts["claims"] += 1
        claim_id_map[rel["id"]] = claim.id

        if rel.get("excerpt") and db_source_id:
            chunk = EvidenceChunk(
                source_id=db_source_id,
                text=rel["excerpt"],
                section="claim_excerpt",
                embedding=provider.embed(rel["excerpt"]),
                chunk_metadata={"claim_id": claim.id},
            )
            db.add(chunk)
            db.flush()
            claim.evidence_chunk_id = chunk.id
            counts["chunks"] += 1

        edge = KnowledgeEdge(
            source_node_id=from_id,
            target_node_id=to_id,
            relation_type=rel["relation_type"],
            mechanism=rel["claim_text"],
            conditions=rel.get("conditions", []),
            source_claim_id=claim.id,
            evidence_strength=rel["evidence_strength"],
            limitations=rel.get("limitations"),
        )
        db.add(edge)
        counts["edges"] += 1

    # 3. Interventions
    for row in _load_json("interventions.json"):
        get_or_create_node(row["id"], "intervention")
        claim_ids = [claim_id_map[eid] for eid in row.get("source_claim_ids", []) if eid in claim_id_map]
        intervention = Intervention(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            target_metrics=row.get("target_metrics", []),
            prerequisites=row.get("prerequisites", []),
            constraints=row.get("constraints", {}),
            ecosystem_context=row.get("ecosystem_context", []),
            source_claim_ids=claim_ids,
            water_sensitivity=row.get("water_sensitivity"),
            typical_time_horizon=row.get("typical_time_horizon"),
        )
        db.merge(intervention)
        counts["interventions"] += 1

    db.commit()
    logger.info("Seed complete: %s", counts)
    return counts
