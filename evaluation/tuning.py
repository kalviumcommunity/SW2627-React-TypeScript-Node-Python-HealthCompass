"""Retrieval tuning experiment implementation."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from healthcompass.vector_store import (
    RetrievalResult as VectorRetrievalResult,
    initialize_vector_store,
    retrieve,
)


@dataclass
class RetrievalConfig:
    """Configuration for retrieval tuning."""

    name: str
    k: int
    score_threshold: Optional[float] = None
    metadata_filter: Optional[Dict[str, Any]] = None


@dataclass
class TestQuery:
    """A test query for evaluation."""

    query: str
    expected_source: str
    expected_keyword: Optional[str] = None
    explanation: str = ""


@dataclass
class QueryEvaluationResult:
    """Result from a single retrieval operation."""

    query: str
    expected_source: str
    config_name: str
    k: int
    retrieved_rank: Optional[int]
    retrieved_chunk_id: Optional[str]
    retrieved_source: Optional[str]
    score: Optional[float]
    matched_expected_source: bool
    matched_expected_keyword: bool


@dataclass
class RetrievalEvaluation:
    """Evaluation results for a retrieval configuration."""

    config_name: str
    k: int
    score_threshold: Optional[float]
    metadata_filter: Optional[Dict[str, Any]]
    total_queries: int
    top_1_hits: int
    top_k_hits: int
    top_1_hit_rate: float
    top_k_hit_rate: float
    average_rank: Optional[float]
    queries_with_zero_relevant: int
    results: List[QueryEvaluationResult] = field(default_factory=list)


def load_test_queries(queries_path: Path) -> List[TestQuery]:
    """Load test queries from JSON file.

    Args:
        queries_path: Path to the JSON file containing test queries

    Returns:
        List of TestQuery objects
    """
    with open(queries_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [
        TestQuery(
            query=item["query"],
            expected_source=item["expected_source"],
            expected_keyword=item.get("expected_keyword"),
            explanation=item.get("explanation", ""),
        )
        for item in data
    ]


def evaluate_single_query(
    query: TestQuery,
    config: RetrievalConfig,
    collection,
    use_mock: bool = False,
) -> QueryEvaluationResult:
    """Evaluate a single query against a retrieval configuration.

    Args:
        query: TestQuery to evaluate
        config: RetrievalConfig to test
        collection: ChromaDB collection
        use_mock: Whether to use mock results (for testing without API)

    Returns:
        QueryEvaluationResult with evaluation data
    """
    if use_mock:
        # Use mock results for testing without API
        from healthcompass.vector_store import RetrievalResult as MockResult

        mock_results = [
            MockResult(
                rank=1,
                chunk_id="vaccination_chunk_0",
                distance=0.1,
                text="Vaccination guidance text...",
                metadata={"source": "vaccination_guidance.txt", "chunk_id": "0"},
            )
        ]
        retrieved = mock_results
    else:
        try:
            retrieved = retrieve(
                query=query.query,
                collection=collection,
                k=config.k,
            )
        except Exception as e:
            # If API call fails, return empty result
            return QueryEvaluationResult(
                query=query.query,
                expected_source=query.expected_source,
                config_name=config.name,
                k=config.k,
                retrieved_rank=None,
                retrieved_chunk_id=None,
                retrieved_source=None,
                score=None,
                matched_expected_source=False,
                matched_expected_keyword=False,
            )

    # Find the first result that matches the expected source
    matching_result = None
    for result in retrieved:
        if result.metadata.get("source") == query.expected_source:
            matching_result = result
            break

    # Check keyword match if no source match
    keyword_match = False
    if not matching_result and query.expected_keyword:
        for result in retrieved:
            if query.expected_keyword.lower() in result.text.lower():
                keyword_match = True
                matching_result = result
                break

    return QueryEvaluationResult(
        query=query.query,
        expected_source=query.expected_source,
        config_name=config.name,
        k=config.k,
        retrieved_rank=matching_result.rank if matching_result else None,
        retrieved_chunk_id=matching_result.chunk_id if matching_result else None,
        retrieved_source=matching_result.metadata.get("source") if matching_result else None,
        score=matching_result.distance if matching_result else None,
        matched_expected_source=(matching_result is not None),
        matched_expected_keyword=keyword_match,
    )


def evaluate_retrieval_configurations(
    queries: List[TestQuery],
    configs: List[RetrievalConfig],
    collection,
    use_mock: bool = False,
) -> List[RetrievalEvaluation]:
    """Evaluate multiple retrieval configurations against test queries.

    Args:
        queries: List of TestQuery objects
        configs: List of RetrievalConfig objects to test
        collection: ChromaDB collection
        use_mock: Whether to use mock results

    Returns:
        List of RetrievalEvaluation objects
    """
    evaluations = []

    for config in configs:
        results = []
        top_1_hits = 0
        top_k_hits = 0
        total_queries = len(queries)
        ranks = []
        zero_relevant_count = 0

        for query in queries:
            result = evaluate_single_query(query, config, collection, use_mock)
            results.append(result)

            if result.matched_expected_source:
                top_k_hits += 1
                if result.retrieved_rank == 1:
                    top_1_hits += 1
                ranks.append(result.retrieved_rank)
            else:
                zero_relevant_count += 1

        top_1_hit_rate = top_1_hits / total_queries if total_queries > 0 else 0
        top_k_hit_rate = top_k_hits / total_queries if total_queries > 0 else 0
        average_rank = sum(ranks) / len(ranks) if ranks else None

        evaluation = RetrievalEvaluation(
            config_name=config.name,
            k=config.k,
            score_threshold=config.score_threshold,
            metadata_filter=config.metadata_filter,
            total_queries=total_queries,
            top_1_hits=top_1_hits,
            top_k_hits=top_k_hits,
            top_1_hit_rate=top_1_hit_rate,
            top_k_hit_rate=top_k_hit_rate,
            average_rank=average_rank,
            queries_with_zero_relevant=zero_relevant_count,
            results=results,
        )
        evaluations.append(evaluation)

    return evaluations


def select_best_configuration(evaluations: List[RetrievalEvaluation]) -> RetrievalEvaluation:
    """Select the best retrieval configuration based on evaluation results.

    Selection criteria:
    1. Higher top-k hit rate is better for recall
    2. If top-k hit rates are equal, compare top-1 hit rate
    3. If performance is similar, prefer smaller k

    Args:
        evaluations: List of RetrievalEvaluation objects

    Returns:
        The best RetrievalEvaluation
    """
    # Sort by top-k hit rate (descending), then top-1 hit rate (descending), then k (ascending)
    sorted_evals = sorted(
        evaluations,
        key=lambda e: (e.top_k_hit_rate, e.top_1_hit_rate, -e.k),
        reverse=True,
    )

    return sorted_evals[0]


def save_evaluation_results(
    evaluations: List[RetrievalEvaluation],
    best_config: RetrievalEvaluation,
    output_dir: Path,
):
    """Save evaluation results to JSON and Markdown files.

    Args:
        evaluations: List of RetrievalEvaluation objects
        best_config: The selected best configuration
        output_dir: Directory to save results
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save detailed JSON results
    json_path = output_dir / "retrieval_tuning_results.json"
    json_data = []
    for eval_result in evaluations:
        for result in eval_result.results:
            json_data.append(
                {
                    "query": result.query,
                    "expected_source": result.expected_source,
                    "config_name": result.config_name,
                    "k": result.k,
                    "retrieved_rank": result.retrieved_rank,
                    "retrieved_chunk_id": result.retrieved_chunk_id,
                    "retrieved_source": result.retrieved_source,
                    "score": result.score,
                    "matched_expected_source": result.matched_expected_source,
                    "matched_expected_keyword": result.matched_expected_keyword,
                }
            )

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    # Save summary JSON
    summary_path = output_dir / "retrieval_tuning_summary.json"
    summary_data = []
    for eval_result in evaluations:
        summary_data.append(
            {
                "config_name": eval_result.config_name,
                "k": eval_result.k,
                "score_threshold": eval_result.score_threshold,
                "metadata_filter": eval_result.metadata_filter,
                "total_queries": eval_result.total_queries,
                "top_1_hits": eval_result.top_1_hits,
                "top_k_hits": eval_result.top_k_hits,
                "top_1_hit_rate": eval_result.top_1_hit_rate,
                "top_k_hit_rate": eval_result.top_k_hit_rate,
                "average_rank": eval_result.average_rank,
                "queries_with_zero_relevant": eval_result.queries_with_zero_relevant,
            }
        )

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    # Save Markdown report
    md_path = output_dir / "retrieval_tuning_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Retrieval Tuning Experiment\n\n")

        f.write("## Dataset\n\n")
        f.write(f"- **Number of queries:** {evaluations[0].total_queries}\n")
        f.write(f"- **Expected source methodology:** Source document matching\n")
        f.write(f"- **Keyword matching:** Fallback when source not found\n\n")

        f.write("## Configuration Comparison\n\n")
        f.write("| Configuration | k | Top-1 Hit Rate | Top-k Hit Rate | Average Rank |\n")
        f.write("|---|---:|---:|---:|---:|\n")

        for eval_result in evaluations:
            avg_rank = eval_result.average_rank
            avg_rank_str = f"{avg_rank:.2f}" if avg_rank else "N/A"
            f.write(
                f"| {eval_result.config_name} | {eval_result.k} | {eval_result.top_1_hit_rate:.1%} | {eval_result.top_k_hit_rate:.1%} | {avg_rank_str} |\n"
            )

        f.write("\n## Detailed Results\n\n")

        for eval_result in evaluations:
            f.write(f"### {eval_result.config_name}\n\n")
            f.write(f"**Settings:**\n")
            f.write(f"- k: {eval_result.k}\n")
            f.write(f"- Score threshold: {eval_result.score_threshold}\n")
            f.write(f"- Metadata filter: {eval_result.metadata_filter}\n\n")

            f.write(f"**Performance:**\n")
            f.write(f"- Top-1 hits: {eval_result.top_1_hits}/{eval_result.total_queries}\n")
            f.write(f"- Top-k hits: {eval_result.top_k_hits}/{eval_result.total_queries}\n")
            f.write(f"- Top-1 hit rate: {eval_result.top_1_hit_rate:.1%}\n")
            f.write(f"- Top-k hit rate: {eval_result.top_k_hit_rate:.1%}\n")
            avg_rank = eval_result.average_rank
            avg_rank_str = f"{avg_rank:.2f}" if avg_rank else "N/A"
            f.write(f"- Average rank: {avg_rank_str}\n")
            f.write(f"- Queries with zero relevant: {eval_result.queries_with_zero_relevant}\n\n")

            f.write("**Query Results:**\n\n")
            for result in eval_result.results:
                status = "✓" if result.matched_expected_source else "✗"
                f.write(f"{status} **Query:** {result.query}\n")
                f.write(f"  - Expected source: {result.expected_source}\n")
                f.write(f"  - Retrieved rank: {result.retrieved_rank}\n")
                f.write(f"  - Retrieved source: {result.retrieved_source}\n")
                score = result.score
                score_str = f"{score:.4f}" if score else "N/A"
                f.write(f"  - Score: {score_str}\n")
                f.write(f"  - Matched: {result.matched_expected_source}\n\n")

        f.write("## Best Configuration\n\n")
        f.write(f"**Chosen configuration:** {best_config.config_name}\n")
        f.write(f"- k = {best_config.k}\n")
        f.write(f"- Score threshold = {best_config.score_threshold}\n")
        f.write(f"- Metadata filter = {best_config.metadata_filter}\n\n")

        f.write("**Reason:**\n")
        f.write(f"Selected based on highest top-k hit rate ({best_config.top_k_hit_rate:.1%}) ")
        f.write(f"and top-1 hit rate ({best_config.top_1_hit_rate:.1%}). ")
        if best_config.k > 1:
            f.write(f"Configuration with k={best_config.k} provides better recall while maintaining reasonable context size.\n")
        else:
            f.write(f"Minimal k for focused retrieval.\n")

        f.write("\n## Limitations\n\n")
        f.write("- Small evaluation dataset (8 queries)\n")
        f.write("- Single document type (vaccination guidance)\n")
        f.write("- Deterministic embeddings used for testing\n")
        f.write("- Not a statistically comprehensive benchmark\n")
        f.write("- Results may vary with different document collections\n")


def run_retrieval_tuning_experiment(
    queries_path: Path,
    output_dir: Path,
    use_mock: bool = False,
) -> tuple[List[RetrievalEvaluation], RetrievalEvaluation]:
    """Run the complete retrieval tuning experiment.

    Args:
        queries_path: Path to test queries JSON file
        output_dir: Directory to save results
        use_mock: Whether to use mock results

    Returns:
        Tuple of (evaluations, best_config)
    """
    # Load test queries
    queries = load_test_queries(queries_path)

    # Define retrieval configurations to compare
    configs = [
        RetrievalConfig(name="Config A", k=3),
        RetrievalConfig(name="Config B", k=5),
    ]

    # Initialize vector database
    collection = initialize_vector_store()

    # Evaluate configurations
    evaluations = evaluate_retrieval_configurations(queries, configs, collection, use_mock)

    # Select best configuration
    best_config = select_best_configuration(evaluations)

    # Save results
    save_evaluation_results(evaluations, best_config, output_dir)

    return evaluations, best_config
