"""Document/text ingestion into the evidence store.

Splits text into meaningful chunks, generates embeddings, and creates
ScientificSource + EvidenceChunk rows. Used both by the seed loader and by
POST /api/v1/knowledge/ingest for user-supplied text/JSON records.

Ingestion never invents metadata: fields the caller does not provide are left
null, and the resulting source is marked ``is_verified=False`` unless the
caller explicitly asserts verification, which keeps unverified user uploads
visibly distinct from the curated seed corpus.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.ai.embeddings import get_embedding_provider
from app.models.evidence import EvidenceChunk, ScientificSource

_CHUNK_TARGET_CHARS = 700


@dataclass
class IngestionResult:
    source_id: str
    chunk_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def chunk_text(text: str, target_chars: int = _CHUNK_TARGET_CHARS) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else []

    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if buf and len(buf) + len(para) + 1 > target_chars:
            chunks.append(buf.strip())
            buf = para
        else:
            buf = f"{buf}\n\n{para}" if buf else para
    if buf.strip():
        chunks.append(buf.strip())
    return chunks


def ingest_source(
    db: Session,
    *,
    title: str,
    text: str | None,
    authors: list[str] | None = None,
    organization: str | None = None,
    publication_year: int | None = None,
    doi: str | None = None,
    url: str | None = None,
    source_type: str = "user_uploaded",
    abstract: str | None = None,
    ecosystem_context: list[str] | None = None,
    limitations: str | None = None,
    is_verified: bool = False,
) -> IngestionResult:
    warnings: list[str] = []
    if not text and not abstract:
        warnings.append(
            "No full text or abstract supplied; source stored as metadata-only and cannot be used for "
            "semantic evidence retrieval until text is added."
        )

    source = ScientificSource(
        title=title,
        authors=authors or [],
        organization=organization,
        publication_year=publication_year,
        doi=doi,
        url=url,
        source_type=source_type,
        abstract=abstract,
        full_text_available=bool(text),
        ecosystem_context=ecosystem_context or [],
        limitations=limitations,
        is_verified=is_verified,
        ingestion_status="ingested" if (text or abstract) else "metadata_only",
    )
    db.add(source)
    db.flush()

    provider = get_embedding_provider()
    chunk_ids: list[str] = []
    content_for_chunks = text or abstract or ""
    for raw_chunk in chunk_text(content_for_chunks):
        embedding = provider.embed(raw_chunk)
        chunk = EvidenceChunk(source_id=source.id, text=raw_chunk, embedding=embedding)
        db.add(chunk)
        db.flush()
        chunk_ids.append(chunk.id)

    if not chunk_ids:
        warnings.append("Ingestion produced zero evidence chunks; check that source text was non-empty.")

    return IngestionResult(source_id=source.id, chunk_ids=chunk_ids, warnings=warnings)
