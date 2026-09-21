from __future__ import annotations

import heapq
import math
from typing import Sequence


def is_unit_vector(vec: Sequence[float], tol: float = 1e-3) -> bool:
    """Checks whether the vector has euclidean norm approx 1.0."""
    if not vec:
        return False
    norm_sq = sum(x * x for x in vec)
    return abs(norm_sq - 1.0) < tol


def fast_cosine_similarity(a: Sequence[float], b: Sequence[float], assumed_normalized: bool = True) -> float:
    """Computes cosine similarity between two vectors.

    If vectors are already normalized to unit length, this performs an O(d) dot product
    without redundant square roots.
    """
    if not a or not b or len(a) != len(b):
        return 0.0

    if assumed_normalized:
        dot = sum(x * y for x, y in zip(a, b))
        return max(-1.0, min(1.0, dot))

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm_a * norm_b)))


def batch_top_k_similarities(
    query_vec: Sequence[float],
    candidate_vecs: list[tuple[str, Sequence[float]]],
    top_k: int = 5,
) -> list[tuple[str, float]]:
    """Calculates top-k highest similarity candidate vectors efficiently."""
    if not query_vec or not candidate_vecs or top_k <= 0:
        return []

    scores: list[tuple[float, str]] = []
    for cid, vec in candidate_vecs:
        score = fast_cosine_similarity(query_vec, vec, assumed_normalized=True)
        scores.append((score, cid))

    top_matches = heapq.nlargest(top_k, scores, key=lambda item: item[0])
    return [(cid, score) for score, cid in top_matches]
