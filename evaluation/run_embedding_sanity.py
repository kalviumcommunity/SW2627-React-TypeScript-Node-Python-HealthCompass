"""Run quick embedding sanity checks against the configured Chroma collection."""

import os
from pathlib import Path

from evaluation.embedding_sanity import (
    SanityTestCase,
    format_sanity_report,
    run_embedding_sanity_checks,
)
from evaluation.evaluate_retrieval import load_labelled_queries
from healthcompass.vector_store import embed_query, initialize_vector_store


def main() -> int:
    """Run source-based checks and return a non-zero status if any fail."""
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is required to embed sanity-check queries.")
        return 2

    collection = initialize_vector_store()
    stored = collection.get(include=["embeddings", "documents", "metadatas"])
    if not stored["ids"]:
        print("No chunks found in the configured vector collection.")
        return 2

    chunk_records = []
    for embedding, text, metadata in zip(
        stored["embeddings"], stored["documents"], stored["metadatas"], strict=True
    ):
        vector = embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
        chunk_records.append(
            {
                "embedding": vector,
                "text": text,
                "source": metadata.get("source", "unknown"),
                "metadata": metadata,
            }
        )

    query_path = Path(__file__).parent / "labelled_queries.json"
    labelled_queries = load_labelled_queries(query_path)
    test_cases = [
        SanityTestCase(query=item.query, expected_source=item.relevant_source)
        for item in labelled_queries
        if item.relevant_source
    ]
    report = run_embedding_sanity_checks(
        test_cases,
        chunk_records,
        embed_query,
        top_k=min(3, len(chunk_records)),
    )
    print(format_sanity_report(report))
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
