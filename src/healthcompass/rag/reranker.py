"""Chunk re-ranking module for HealthCompass RAG system."""

import re
from typing import List, Optional

from healthcompass.vector_store import RetrievalResult


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric words."""
    return re.findall(r"\w+", text.casefold())


def compute_lexical_score(query: str, text: str) -> float:
    """Compute lexical matching score based on term overlap and phrase proximity.

    Args:
        query: Search query string.
        text: Target document chunk text.

    Returns:
        Score between 0.0 and 1.0.
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return 0.0

    text_tokens = _tokenize(text)
    if not text_tokens:
        return 0.0

    text_token_set = set(text_tokens)
    query_token_set = set(query_tokens)

    # 1. Term overlap (recall of query words)
    overlap = len(query_token_set & text_token_set) / len(query_token_set)

    # 2. Exact phrase match bonus
    phrase_bonus = 0.0
    clean_query = query.strip().casefold()
    clean_text = text.casefold()
    if len(query_tokens) > 1 and clean_query in clean_text:
        phrase_bonus = 0.3
    elif any(
        f"{query_tokens[i]} {query_tokens[i+1]}" in clean_text
        for i in range(len(query_tokens) - 1)
    ):
        phrase_bonus = 0.15

    # 3. Term frequency density (frequency of query terms in text)
    matched_freq = sum(1 for token in text_tokens if token in query_token_set)
    density = min(1.0, matched_freq / max(len(text_tokens), 1) * 3)

    score = 0.6 * overlap + 0.25 * phrase_bonus + 0.15 * density
    return min(1.0, max(0.0, score))


def rerank_chunks(
    query: str,
    candidates: List[RetrievalResult],
    top_k: Optional[int] = None,
    weight_semantic: float = 0.6,
    weight_lexical: float = 0.4,
) -> List[RetrievalResult]:
    """Re-rank candidate retrieval results using blended semantic and lexical scoring.

    Args:
        query: Original user query.
        candidates: List of initial RetrievalResult candidates.
        top_k: Optional number of top results to return. If None, returns all candidates re-ordered.
        weight_semantic: Relative weight for vector similarity score (0.0 to 1.0).
        weight_lexical: Relative weight for lexical relevance score (0.0 to 1.0).

    Returns:
        List of re-ranked RetrievalResult instances with updated rank.
    """
    if not candidates:
        return []

    if top_k is not None and top_k <= 0:
        raise ValueError(f"top_k must be greater than 0, got {top_k}")

    if not (0.0 <= weight_semantic <= 1.0) or not (0.0 <= weight_lexical <= 1.0):
        raise ValueError("Weights must be between 0.0 and 1.0")

    total_weight = weight_semantic + weight_lexical
    if total_weight <= 0:
        norm_sem, norm_lex = 0.5, 0.5
    else:
        norm_sem = weight_semantic / total_weight
        norm_lex = weight_lexical / total_weight

    scored_candidates = []
    for candidate in candidates:
        # Distance to similarity: smaller distance is better
        # Chroma L2 or cosine distance typically ranges 0 to 2
        semantic_sim = 1.0 / (1.0 + max(0.0, float(candidate.distance)))
        lexical_sim = compute_lexical_score(query, candidate.text)

        rerank_score = (norm_sem * semantic_sim) + (norm_lex * lexical_sim)
        scored_candidates.append((rerank_score, candidate))

    # Sort descending by re-rank score
    scored_candidates.sort(key=lambda item: item[0], reverse=True)

    limit = top_k if top_k is not None else len(scored_candidates)
    reranked_results = []
    for rank, (score, cand) in enumerate(scored_candidates[:limit], start=1):
        reranked_results.append(
            RetrievalResult(
                rank=rank,
                chunk_id=cand.chunk_id,
                distance=cand.distance,
                text=cand.text,
                metadata=dict(cand.metadata),
                hybrid_score=round(score, 4),
            )
        )

    return reranked_results
