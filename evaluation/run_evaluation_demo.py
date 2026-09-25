"""Run retrieval evaluation with deterministic embeddings for demonstration.

This script uses deterministic embeddings based on query hash to demonstrate
the evaluation pipeline without requiring a live API key. For production use,
use run_evaluation.py with actual API calls.
"""

from pathlib import Path

from evaluation.evaluate_retrieval import (
    evaluate_retrieval,
    load_labelled_queries,
    save_evaluation_results,
)


def evaluate_with_deterministic_embeddings():
    """Run evaluation with deterministic embeddings for demonstration."""
    # Load labelled queries
    queries_path = Path(__file__).parent / "labelled_queries.json"
    queries = load_labelled_queries(queries_path)

    print(f"Loaded {len(queries)} labelled queries")
    print("Evaluating at k values: 1, 3, 5")
    print()
    print("NOTE: Using deterministic embeddings for demonstration.")
    print("      Results may not reflect actual semantic similarity.")
    print("      For production evaluation, use run_evaluation.py with a live API key.")
    print()

    # Run evaluation with deterministic embeddings
    k_values = [1, 3, 5]
    summary = evaluate_retrieval(queries, k_values, use_deterministic_embeddings=True)

    # Print summary
    print("=== Evaluation Summary ===")
    print(f"Total queries: {summary.total_queries}")
    print()
    print("Metrics:")
    print(f"  Recall@1: {summary.recall_at_1:.2%}")
    print(f"  Recall@3: {summary.recall_at_3:.2%}")
    print(f"  Recall@5: {summary.recall_at_5:.2%}")
    print(f"  Precision@1: {summary.precision_at_1:.2%}")
    print(f"  Precision@3: {summary.precision_at_3:.2%}")
    print(f"  Precision@5: {summary.precision_at_5:.2%}")
    print()
    print(f"Failures detected: {len(summary.failures)}")
    print()

    # Save results
    output_dir = Path(__file__).parent / "results"
    json_path, md_path = save_evaluation_results(summary, output_dir, use_deterministic_embeddings=True)

    print("Results saved:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")


if __name__ == "__main__":
    evaluate_with_deterministic_embeddings()
