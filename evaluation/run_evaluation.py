"""Run retrieval evaluation with Recall@k and Precision@k metrics."""

import os
from pathlib import Path

from evaluation.evaluate_retrieval import (
    evaluate_retrieval,
    load_labelled_queries,
    save_evaluation_results,
)


def main():
    """Run the retrieval evaluation."""
    # Check for API key
    api_key_available = bool(os.getenv("OPENAI_API_KEY"))

    if not api_key_available:
        print("WARNING: OPENAI_API_KEY is not set.")
        print("The evaluation requires a live API key for query embedding.")
        print("Please set OPENAI_API_KEY in your .env file or environment variables.")
        print()
        print("For testing without an API key, use the unit tests instead:")
        print("  pytest tests/test_retrieval_evaluation.py")
        return

    # Load labelled queries
    queries_path = Path(__file__).parent / "labelled_queries.json"
    queries = load_labelled_queries(queries_path)

    print(f"Loaded {len(queries)} labelled queries")
    print("Evaluating at k values: 1, 3, 5")
    print()

    # Run evaluation
    k_values = [1, 3, 5]
    summary = evaluate_retrieval(queries, k_values)

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
    json_path, md_path = save_evaluation_results(summary, output_dir, use_deterministic_embeddings=False)

    print("Results saved:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")


if __name__ == "__main__":
    main()
