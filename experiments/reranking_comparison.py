"""Experiment script demonstrating chunk re-ranking benefits."""

from healthcompass.rag.reranker import rerank_chunks
from healthcompass.vector_store import RetrievalResult


def run_experiment():
    query = "District A fever isolation protocol"

    candidates = [
        RetrievalResult(
            rank=1,
            chunk_id="chunk_gen_1",
            distance=0.15,
            text="District general administration handles operational coordination and staff rosters.",
            metadata={"source": "admin.txt"},
        ),
        RetrievalResult(
            rank=2,
            chunk_id="chunk_iso_2",
            distance=0.28,
            text="District A fever isolation protocol requires patients with acute symptoms to isolate for 7 days.",
            metadata={"source": "outbreak_policy.txt"},
        ),
        RetrievalResult(
            rank=3,
            chunk_id="chunk_med_3",
            distance=0.32,
            text="Fever management protocol for pediatric patients in District B clinics.",
            metadata={"source": "pediatric_guidance.txt"},
        ),
    ]

    print(f"Query: {query}\n")
    print("--- Stage 1: Vector Search Only ---")
    for cand in candidates:
        print(f"Rank {cand.rank} | Chunk: {cand.chunk_id} | Distance: {cand.distance:.3f}")
        print(f"  Snippet: {cand.text[:70]}...")

    reranked = rerank_chunks(query, candidates, top_k=2)

    print("\n--- Stage 2: Re-ranked Results (Top 2) ---")
    for cand in reranked:
        print(f"Rank {cand.rank} | Chunk: {cand.chunk_id} | Hybrid Score: {cand.hybrid_score}")
        print(f"  Snippet: {cand.text[:70]}...")


if __name__ == "__main__":
    run_experiment()
