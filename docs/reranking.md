# Chunk Re-Ranking for Precision

## Overview

In Retrieval-Augmented Generation (RAG), vector similarity search retrieves an initial candidate pool of relevant chunks. However, vector distance alone can miss critical exact term matches (such as guideline revision codes, specific dosages, or district names). 

**Chunk Re-Ranking** introduces a two-stage retrieval architecture:
1. **Stage 1 (High Recall)**: Vector database retrieves $K_{\text{candidates}}$ candidates (e.g., $K=10$).
2. **Stage 2 (High Precision)**: A re-ranking model re-scores and re-orders the candidates using deep lexical matching, exact phrase matches, and term proximity, returning the top $k$ (e.g., $k=3$) to the LLM context.

## Two-Stage Architecture

```
User Query
    │
    ▼
Stage 1: Vector Search (High Recall, k=10)
    │
    ▼
Candidate Chunks [c1, c2, c3, ..., c10]
    │
    ▼
Stage 2: Re-Ranking Engine (Hybrid Lexical-Semantic Fusion)
    │
    ▼
Top-K Chunks for Prompt Injection (k=3)
```

## Scoring Formula

For each candidate chunk $c$ and query $q$:

$$S_{\text{semantic}}(c) = \frac{1}{1 + \text{distance}(q, c)}$$

$$S_{\text{lexical}}(q, c) = 0.6 \cdot \text{Overlap}(q, c) + 0.25 \cdot \text{PhraseBonus}(q, c) + 0.15 \cdot \text{Density}(q, c)$$

$$S_{\text{rerank}}(q, c) = w_{\text{semantic}} \cdot S_{\text{semantic}}(c) + w_{\text{lexical}} \cdot S_{\text{lexical}}(q, c)$$

## Usage in HealthCompass

```python
from healthcompass.rag.reranker import rerank_chunks
from healthcompass.vector_store import retrieve

# Stage 1: Retrieve candidate pool
candidates = retrieve(query, collection, k=10)

# Stage 2: Re-rank to top 3 for context injection
reranked_chunks = rerank_chunks(
    query=query,
    candidates=candidates,
    top_k=3,
    weight_semantic=0.6,
    weight_lexical=0.4,
)
```
