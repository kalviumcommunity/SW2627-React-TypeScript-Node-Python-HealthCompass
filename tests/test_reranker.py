"""Unit tests for chunk re-ranking module."""

import pytest

from healthcompass.rag.reranker import compute_lexical_score, rerank_chunks
from healthcompass.vector_store import RetrievalResult


def test_compute_lexical_score_empty_inputs():
    assert compute_lexical_score("", "some document text") == 0.0
    assert compute_lexical_score("query", "") == 0.0


def test_compute_lexical_score_exact_phrase():
    score_exact = compute_lexical_score("isolation protocol", "Follow the isolation protocol immediately.")
    score_unrelated = compute_lexical_score("isolation protocol", "General hospital billing guidelines.")
    assert score_exact > score_unrelated
    assert score_exact > 0.5


def test_rerank_chunks_promotes_exact_keyword_match():
    # Candidate 1: slightly lower vector distance, but text is general
    cand_1 = RetrievalResult(
        rank=1,
        chunk_id="chunk_1",
        distance=0.2,
        text="General pandemic procedures and administrative guidelines.",
        metadata={"source": "admin.pdf"},
    )
    # Candidate 2: higher vector distance, but contains exact answer terms
    cand_2 = RetrievalResult(
        rank=2,
        chunk_id="chunk_2",
        distance=0.4,
        text="District A emergency isolation protocol requires 10 days quarantine.",
        metadata={"source": "isolation_policy.pdf"},
    )

    query = "isolation protocol District A"
    reranked = rerank_chunks(query, [cand_1, cand_2], top_k=2, weight_semantic=0.3, weight_lexical=0.7)

    assert len(reranked) == 2
    assert reranked[0].chunk_id == "chunk_2"
    assert reranked[0].rank == 1
    assert reranked[1].chunk_id == "chunk_1"
    assert reranked[1].rank == 2


def test_rerank_chunks_top_k_limits_output():
    candidates = [
        RetrievalResult(rank=i, chunk_id=f"c_{i}", distance=0.1 * i, text=f"Text {i}", metadata={})
        for i in range(1, 6)
    ]
    reranked = rerank_chunks("Text 1", candidates, top_k=3)
    assert len(reranked) == 3


def test_rerank_chunks_empty_candidates():
    assert rerank_chunks("query", []) == []


def test_rerank_chunks_invalid_args():
    cand = RetrievalResult(rank=1, chunk_id="c1", distance=0.1, text="text", metadata={})
    with pytest.raises(ValueError, match="top_k must be greater than 0"):
        rerank_chunks("query", [cand], top_k=0)

    with pytest.raises(ValueError, match="Weights must be between 0.0 and 1.0"):
        rerank_chunks("query", [cand], weight_semantic=1.5)
