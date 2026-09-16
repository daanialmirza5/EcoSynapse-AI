"""Hybrid evidence retrieval: semantic (embedding cosine similarity) + lexical
(keyword overlap) + knowledge-graph term expansion, merged and reranked.

This directly implements the retrieval pipeline required by the challenge
(section 8): parse -> identify entities -> expand via graph -> semantic
search -> lexical search -> merge/dedupe -> rerank -> return sources +
excerpts + relevance rationale. Every step is inspectable via
``retrieve_with_trace`` so the API can expose a full retrieval trace.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.ai.embeddings import cosine_similarity, get_embedding_provider
from app.knowledge.graph import build_graph, neighbors_within_hops
from app.knowledge.vocabulary import match_nodes_in_text
from app.models.evidence import EvidenceChunk, ScientificSource
from app.models.profile import EnvironmentalProfile

_WORD_RE = re.compile(r"[a-zA-Z]{3,}")


@dataclass
class RetrievedItem:
    chunk_id: str
    source: ScientificSource
    excerpt: str
    relevance_score: float
    match_reasons: list[str] = field(default_factory=list)


@dataclass
class RetrievalTraceResult:
    query: str
    expanded_terms: list[str]
    graph_concepts: list[str]
    semantic_candidates: int
    lexical_candidates: int
    merged_candidates: int
    results: list[RetrievedItem]


def _lexical_score(query_tokens: set[str], chunk_text: str) -> float:
    chunk_tokens = set(t.lower() for t in _WORD_RE.findall(chunk_text))
    if not query_tokens or not chunk_tokens:
        return 0.0
    overlap = query_tokens & chunk_tokens
    return len(overlap) / len(query_tokens)


def retrieve_with_trace(
    db: Session,
    query: str,
    profile: EnvironmentalProfile | None = None,
    extra_concepts: list[str] | None = None,
    top_k: int = 6,
) -> RetrievalTraceResult:
    # 1-2. Parse question, identify entities/metrics
    matched_concepts = match_nodes_in_text(query)
    if profile is not None:
        profile_text = " ".join(
            filter(
                None,
                [
                    profile.ecosystem_type,
                    profile.land_use_type,
                    profile.region,
                    profile.rainfall_qualitative,
                ],
            )
        )
        matched_concepts.extend(match_nodes_in_text(profile_text))
    if extra_concepts:
        matched_concepts.extend(extra_concepts)
    matched_concepts = list(dict.fromkeys(matched_concepts))

    # 3. Expand via knowledge graph (1-hop neighbors of matched concepts)
    graph = build_graph(db)
    expanded = neighbors_within_hops(graph, matched_concepts, hops=1) if matched_concepts else set()
    expanded_terms = sorted(expanded | set(matched_concepts))

    # 4. Semantic vector search
    provider = get_embedding_provider()
    query_vec = provider.embed(query + " " + " ".join(expanded_terms))
    all_chunks = db.query(EvidenceChunk).all()
    semantic_scores: dict[str, float] = {}
    for chunk in all_chunks:
        if chunk.embedding:
            semantic_scores[chunk.id] = cosine_similarity(query_vec, chunk.embedding)
    semantic_candidates = sum(1 for v in semantic_scores.values() if v > 0.05)

    # 5-6. Lexical keyword retrieval
    query_tokens = set(t.lower() for t in _WORD_RE.findall(query)) | set(
        t for term in expanded_terms for t in term.split("_")
    )
    lexical_scores: dict[str, float] = {}
    for chunk in all_chunks:
        score = _lexical_score(query_tokens, chunk.text)
        if score > 0:
            lexical_scores[chunk.id] = score
    lexical_candidates = len(lexical_scores)

    # 7. Merge and dedupe (weighted sum), 8. rerank
    combined: dict[str, float] = {}
    for chunk in all_chunks:
        sem = semantic_scores.get(chunk.id, 0.0)
        lex = lexical_scores.get(chunk.id, 0.0)
        if sem <= 0.0 and lex <= 0.0:
            continue
        combined[chunk.id] = 0.65 * sem + 0.35 * lex

    ranked_ids = sorted(combined.keys(), key=lambda cid: combined[cid], reverse=True)[: top_k * 2]
    chunk_by_id = {c.id: c for c in all_chunks}
    source_by_id = {s.id: s for s in db.query(ScientificSource).all()}

    results: list[RetrievedItem] = []
    for cid in ranked_ids:
        chunk = chunk_by_id[cid]
        source = source_by_id.get(chunk.source_id)
        if source is None:
            continue
        reasons = []
        if semantic_scores.get(cid, 0.0) > 0.15:
            reasons.append(f"semantic similarity {semantic_scores[cid]:.2f} to query concepts")
        if lexical_scores.get(cid, 0.0) > 0.0:
            reasons.append(f"keyword overlap ({lexical_scores[cid]:.2f}) with query terms")
        overlap_concepts = [c for c in expanded_terms if c.replace("_", " ") in chunk.text.lower()]
        if overlap_concepts:
            reasons.append(f"mentions graph concept(s): {', '.join(overlap_concepts[:3])}")
        if not reasons:
            reasons.append("low-confidence residual match")
        results.append(
            RetrievedItem(
                chunk_id=cid,
                source=source,
                excerpt=chunk.text,
                relevance_score=round(combined[cid], 4),
                match_reasons=reasons,
            )
        )
        if len(results) >= top_k:
            break

    return RetrievalTraceResult(
        query=query,
        expanded_terms=expanded_terms,
        graph_concepts=matched_concepts,
        semantic_candidates=semantic_candidates,
        lexical_candidates=lexical_candidates,
        merged_candidates=len(combined),
        results=results,
    )
