import math
import pytest
from app.retrieval.vector_math import is_unit_vector, fast_cosine_similarity, batch_top_k_similarities


def test_is_unit_vector():
    v1 = [1.0, 0.0, 0.0]
    assert is_unit_vector(v1) is True

    inv_sqrt2 = 1.0 / math.sqrt(2)
    v2 = [inv_sqrt2, inv_sqrt2]
    assert is_unit_vector(v2) is True

    v3 = [2.0, 0.0]
    assert is_unit_vector(v3) is False


def test_fast_cosine_similarity():
    # Identical unit vectors -> 1.0
    v1 = [1.0, 0.0, 0.0]
    assert pytest.approx(fast_cosine_similarity(v1, v1), 1e-4) == 1.0

    # Orthogonal -> 0.0
    v2 = [0.0, 1.0, 0.0]
    assert pytest.approx(fast_cosine_similarity(v1, v2), 1e-4) == 0.0

    # Opposite -> -1.0
    v3 = [-1.0, 0.0, 0.0]
    assert pytest.approx(fast_cosine_similarity(v1, v3), 1e-4) == -1.0


def test_batch_top_k_similarities():
    query = [1.0, 0.0, 0.0]
    candidates = [
        ("item_1", [0.0, 1.0, 0.0]),
        ("item_2", [0.8, 0.6, 0.0]),
        ("item_3", [1.0, 0.0, 0.0]),
        ("item_4", [0.5, 0.5, 0.707]),
    ]
    top_2 = batch_top_k_similarities(query, candidates, top_k=2)
    assert len(top_2) == 2
    assert top_2[0][0] == "item_3"  # similarity 1.0
    assert top_2[1][0] == "item_2"  # similarity 0.8
