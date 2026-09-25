"""Retrieval evaluation with Recall@k and Precision@k metrics."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from healthcompass.vector_store import initialize_vector_store, retrieve


@dataclass
class QueryLabel:
    """A labelled query for evaluation."""

    query: str
    relevant_chunk_ids: List[str]
    relevant_source: Optional[str] = None
    explanation: Optional[str] = None
    expected_topic: Optional[str] = None


@dataclass
class RetrievedChunk:
    """A retrieved chunk with relevance status."""

    chunk_id: str
    text: str
    source: str
    distance: float
    is_relevant: bool
    rank: int


@dataclass
class QueryEvaluationResult:
    """Evaluation result for a single query."""

    query: str
    relevant_chunk_ids: List[str]
    k: int
    retrieved_chunks: List[RetrievedChunk]
    recall_at_k: float
    precision_at_k: float
    relevant_retrieved: int
    total_relevant: int
    total_retrieved: int


@dataclass
class EvaluationSummary:
    """Summary of evaluation across all queries."""

    total_queries: int
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    precision_at_1: float
    precision_at_3: float
    precision_at_5: float
    query_results: List[QueryEvaluationResult] = field(default_factory=list)
    failures: List[dict] = field(default_factory=list)


def load_labelled_queries(path: Path) -> List[QueryLabel]:
    """Load labelled queries from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [
        QueryLabel(
            query=item["query"],
            relevant_chunk_ids=item["relevant_chunk_ids"],
            relevant_source=item.get("relevant_source"),
            explanation=item.get("explanation"),
            expected_topic=item.get("expected_topic"),
        )
        for item in data
    ]


def calculate_recall_at_k(
    retrieved_ids: List[str], relevant_ids: List[str]
) -> float:
    """Calculate Recall@k.

    Recall@k = number of relevant chunks retrieved / total number of relevant chunks
    """
    if not relevant_ids:
        return 0.0

    relevant_retrieved = len(set(retrieved_ids) & set(relevant_ids))
    return relevant_retrieved / len(relevant_ids)


def calculate_precision_at_k(
    retrieved_ids: List[str], relevant_ids: List[str]
) -> float:
    """Calculate Precision@k.

    Precision@k = number of relevant chunks retrieved / total chunks retrieved
    """
    if not retrieved_ids:
        return 0.0

    relevant_retrieved = len(set(retrieved_ids) & set(relevant_ids))
    return relevant_retrieved / len(retrieved_ids)


def evaluate_query(
    query_label: QueryLabel, k: int, collection
) -> QueryEvaluationResult:
    """Evaluate a single query with Recall@k and Precision@k.

    Args:
        query_label: The labelled query to evaluate
        k: Number of results to retrieve
        collection: ChromaDB collection

    Raises:
        VectorStoreError: If query embedding fails (e.g., missing API key)
    """
    # Retrieve top-k results
    retrieval_results = retrieve(query_label.query, k=k, collection=collection)

    # Extract retrieved IDs
    retrieved_ids = [r.chunk_id for r in retrieval_results]

    # Build retrieved chunks with relevance status
    retrieved_chunks = []
    for i, result in enumerate(retrieval_results):
        is_relevant = result.chunk_id in query_label.relevant_chunk_ids
        retrieved_chunks.append(
            RetrievedChunk(
                chunk_id=result.chunk_id,
                text=result.text,
                source=result.metadata.get("source", "unknown"),
                distance=result.distance,
                is_relevant=is_relevant,
                rank=i + 1,
            )
        )

    # Calculate metrics
    recall_at_k = calculate_recall_at_k(retrieved_ids, query_label.relevant_chunk_ids)
    precision_at_k = calculate_precision_at_k(
        retrieved_ids, query_label.relevant_chunk_ids
    )

    relevant_retrieved = len(set(retrieved_ids) & set(query_label.relevant_chunk_ids))

    return QueryEvaluationResult(
        query=query_label.query,
        relevant_chunk_ids=query_label.relevant_chunk_ids,
        k=k,
        retrieved_chunks=retrieved_chunks,
        recall_at_k=recall_at_k,
        precision_at_k=precision_at_k,
        relevant_retrieved=relevant_retrieved,
        total_relevant=len(query_label.relevant_chunk_ids),
        total_retrieved=len(retrieved_ids),
    )


def evaluate_query_with_deterministic_embeddings(
    query_label: QueryLabel, k: int, collection
) -> QueryEvaluationResult:
    """Evaluate a single query using deterministic embeddings for demonstration.

    This function uses deterministic embeddings based on query hash to demonstrate
    the evaluation pipeline without requiring a live API key. For production use,
    use evaluate_query() with actual API calls.

    Args:
        query_label: The labelled query to evaluate
        k: Number of results to retrieve
        collection: ChromaDB collection
    """
    # Create deterministic embedding based on query hash
    query_hash = hash(query_label.query) % 1000
    dimension = 1536  # text-embedding-3-small
    query_embedding = [0.001 * (query_hash + j) for j in range(dimension)]

    # Perform similarity search with deterministic embedding
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Process results
    retrieved_ids = results["ids"][0] if results["ids"] else []
    retrieved_chunks = []

    for i, (doc_id, text, metadata, distance) in enumerate(
        zip(
            results["ids"][0] if results["ids"] else [],
            results["documents"][0] if results["documents"] else [],
            results["metadatas"][0] if results["metadatas"] else [],
            results["distances"][0] if results["distances"] else [],
            strict=True,
        )
    ):
        is_relevant = doc_id in query_label.relevant_chunk_ids
        retrieved_chunks.append(
            RetrievedChunk(
                chunk_id=doc_id,
                text=text,
                source=metadata.get("source", "unknown"),
                distance=distance,
                is_relevant=is_relevant,
                rank=i + 1,
            )
        )

    # Calculate metrics
    recall_at_k = calculate_recall_at_k(retrieved_ids, query_label.relevant_chunk_ids)
    precision_at_k = calculate_precision_at_k(
        retrieved_ids, query_label.relevant_chunk_ids
    )

    relevant_retrieved = len(set(retrieved_ids) & set(query_label.relevant_chunk_ids))

    return QueryEvaluationResult(
        query=query_label.query,
        relevant_chunk_ids=query_label.relevant_chunk_ids,
        k=k,
        retrieved_chunks=retrieved_chunks,
        recall_at_k=recall_at_k,
        precision_at_k=precision_at_k,
        relevant_retrieved=relevant_retrieved,
        total_relevant=len(query_label.relevant_chunk_ids),
        total_retrieved=len(retrieved_ids),
    )


def evaluate_retrieval(
    queries: List[QueryLabel], k_values: List[int], use_deterministic_embeddings: bool = False
) -> EvaluationSummary:
    """Evaluate retrieval across all queries and k values.

    Args:
        queries: List of labelled queries to evaluate
        k_values: List of k values to test
        use_deterministic_embeddings: If True, use deterministic embeddings for testing without API key
    """
    collection = initialize_vector_store()

    all_results = []

    for query_label in queries:
        for k in k_values:
            if use_deterministic_embeddings:
                result = evaluate_query_with_deterministic_embeddings(query_label, k, collection)
            else:
                result = evaluate_query(query_label, k, collection)
            all_results.append(result)

    # Calculate aggregate metrics
    # Group by k
    results_by_k = {k: [] for k in k_values}
    for result in all_results:
        results_by_k[result.k].append(result)

    aggregate_metrics = {}
    for k in k_values:
        k_results = results_by_k[k]
        if k_results:
            avg_recall = sum(r.recall_at_k for r in k_results) / len(k_results)
            avg_precision = sum(r.precision_at_k for r in k_results) / len(k_results)
            aggregate_metrics[f"recall_at_{k}"] = avg_recall
            aggregate_metrics[f"precision_at_{k}"] = avg_precision
        else:
            aggregate_metrics[f"recall_at_{k}"] = 0.0
            aggregate_metrics[f"precision_at_{k}"] = 0.0

    # Identify failures (queries with Recall@k < 1.0)
    failures = []
    for result in all_results:
        if result.recall_at_k < 1.0:
            failures.append(
                {
                    "query": result.query,
                    "k": result.k,
                    "recall_at_k": result.recall_at_k,
                    "precision_at_k": result.precision_at_k,
                    "relevant_chunk_ids": result.relevant_chunk_ids,
                    "retrieved_chunk_ids": [c.chunk_id for c in result.retrieved_chunks],
                    "relevant_retrieved": result.relevant_retrieved,
                    "total_relevant": result.total_relevant,
                }
            )

    return EvaluationSummary(
        total_queries=len(queries),
        recall_at_1=aggregate_metrics.get("recall_at_1", 0.0),
        recall_at_3=aggregate_metrics.get("recall_at_3", 0.0),
        recall_at_5=aggregate_metrics.get("recall_at_5", 0.0),
        precision_at_1=aggregate_metrics.get("precision_at_1", 0.0),
        precision_at_3=aggregate_metrics.get("precision_at_3", 0.0),
        precision_at_5=aggregate_metrics.get("precision_at_5", 0.0),
        query_results=all_results,
        failures=failures,
    )


def save_evaluation_results(
    summary: EvaluationSummary, output_dir: Path, use_deterministic_embeddings: bool = False
) -> tuple[Path, Path]:
    """Save evaluation results as JSON and Markdown."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = output_dir / "retrieval_evaluation.json"
    json_data = {
        "total_queries": summary.total_queries,
        "metrics": {
            "recall_at_1": summary.recall_at_1,
            "recall_at_3": summary.recall_at_3,
            "recall_at_5": summary.recall_at_5,
            "precision_at_1": summary.precision_at_1,
            "precision_at_3": summary.precision_at_3,
            "precision_at_5": summary.precision_at_5,
        },
        "query_results": [
            {
                "query": r.query,
                "relevant_chunk_ids": r.relevant_chunk_ids,
                "k": r.k,
                "recall_at_k": r.recall_at_k,
                "precision_at_k": r.precision_at_k,
                "relevant_retrieved": r.relevant_retrieved,
                "total_relevant": r.total_relevant,
                "total_retrieved": r.total_retrieved,
                "retrieved_chunks": [
                    {
                        "chunk_id": c.chunk_id,
                        "text": c.text[:200] + "..." if len(c.text) > 200 else c.text,
                        "source": c.source,
                        "distance": c.distance,
                        "is_relevant": c.is_relevant,
                        "rank": c.rank,
                    }
                    for c in r.retrieved_chunks
                ],
            }
            for r in summary.query_results
        ],
        "failures": summary.failures,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    # Save Markdown
    md_path = output_dir / "retrieval_evaluation_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Retrieval Evaluation\n\n")

        f.write("## Evaluation Dataset\n\n")
        f.write(f"- Number of labelled queries: {summary.total_queries}\n")
        f.write(
            "- k values evaluated: 1, 3, 5\n"
        )
        f.write("- Relevance labels: Created manually based on actual chunk content\n")
        f.write("- Source: vaccination_guidance.txt\n\n")

        f.write("## Metrics\n\n")
        f.write("| Metric | Score |\n")
        f.write("|---|---:|\n")
        f.write(f"| Recall@1 | {summary.recall_at_1:.2%} |\n")
        f.write(f"| Recall@3 | {summary.recall_at_3:.2%} |\n")
        f.write(f"| Recall@5 | {summary.recall_at_5:.2%} |\n")
        f.write(f"| Precision@1 | {summary.precision_at_1:.2%} |\n")
        f.write(f"| Precision@3 | {summary.precision_at_3:.2%} |\n")
        f.write(f"| Precision@5 | {summary.precision_at_5:.2%} |\n\n")

        f.write("## Per-Query Results\n\n")

        # Group results by query
        from collections import defaultdict

        results_by_query = defaultdict(list)
        for result in summary.query_results:
            results_by_query[result.query].append(result)

        for query, results in results_by_query.items():
            f.write(f"### Query: {query}\n\n")
            f.write(f"Relevant chunk IDs: {results[0].relevant_chunk_ids}\n\n")

            for result in results:
                f.write(f"**k = {result.k}**\n\n")
                f.write(f"Recall@{result.k}: {result.recall_at_k:.2%}\n")
                f.write(f"Precision@{result.k}: {result.precision_at_k:.2%}\n\n")
                f.write("Retrieved chunks:\n\n")

                for chunk in result.retrieved_chunks:
                    status = "✓ relevant" if chunk.is_relevant else "✗ not relevant"
                    f.write(
                        f"{chunk.rank}. {chunk.chunk_id} - {status} - distance: {chunk.distance:.4f}\n"
                    )
                    f.write(f"   Source: {chunk.source}\n")
                    f.write(
                        f"   Text: {chunk.text[:150]}{'...' if len(chunk.text) > 150 else ''}\n\n"
                    )

        f.write("## Failure Analysis\n\n")

        if summary.failures:
            for failure in summary.failures:
                f.write(f"### Query: {failure['query']}\n\n")
                f.write(f"k = {failure['k']}\n")
                f.write(f"Recall@{failure['k']}: {failure['recall_at_k']:.2%}\n")
                f.write(f"Precision@{failure['k']}: {failure['precision_at_k']:.2%}\n\n")
                f.write(f"Expected relevant chunks: {failure['relevant_chunk_ids']}\n")
                f.write(f"Retrieved chunks: {failure['retrieved_chunk_ids']}\n")
                f.write(
                    f"Relevant retrieved: {failure['relevant_retrieved']}/{failure['total_relevant']}\n\n"
                )

                # Add analysis based on actual failure
                f.write("**Analysis:**\n\n")
                f.write("**Observed:**\n")
                f.write(f"- Expected {failure['total_relevant']} relevant chunk(s)\n")
                f.write(f"- Retrieved {failure['relevant_retrieved']} relevant chunk(s)\n")
                f.write(f"- Total retrieved: {len(failure['retrieved_chunk_ids'])}\n\n")

                f.write("**Likely cause:**\n")

                # Analyze the failure based on actual data
                if failure["total_relevant"] > 1 and failure["k"] == 1:
                    f.write("k=1 is too small for queries with multiple relevant chunks. ")
                    f.write("The query requires multiple relevant chunks, but only 1 was retrieved.\n\n")
                elif failure["relevant_retrieved"] == 0:
                    f.write("Deterministic embeddings based on query hash do not reflect actual semantic similarity. ")
                    f.write("The wrong chunk was retrieved due to hash-based embedding rather than semantic content.\n\n")
                else:
                    f.write("Deterministic embeddings do not reflect actual semantic similarity.\n\n")

                f.write("**Possible improvement:**\n")

                if failure["total_relevant"] > 1 and failure["k"] == 1:
                    f.write("Increase k to retrieve more chunks when queries have multiple relevant items. ")
                    f.write("For production evaluation, use actual semantic embeddings via OPENAI_API_KEY.\n\n")
                elif failure["relevant_retrieved"] == 0:
                    f.write("Use actual semantic embeddings via OPENAI_API_KEY instead of deterministic hash-based embeddings. ")
                    f.write("This will properly capture semantic similarity between queries and chunks.\n\n")
                else:
                    f.write("Use actual semantic embeddings for production evaluation.\n\n")
        else:
            f.write("No failures detected - all queries achieved perfect recall.\n\n")

        f.write("## Overall Findings\n\n")
        f.write("This evaluation measures the retriever's ability to find relevant chunks using Recall@k and Precision@k metrics.\n\n")

        # Check if this is using deterministic embeddings
        if use_deterministic_embeddings:
            f.write("**IMPORTANT:** This evaluation used deterministic embeddings based on query hash for demonstration purposes.\n")
            f.write("These results do not reflect actual semantic similarity. For production evaluation, use run_evaluation.py with a live OPENAI_API_KEY.\n\n")

        f.write(f"- Average Recall@1: {summary.recall_at_1:.2%}\n")
        f.write(f"- Average Recall@3: {summary.recall_at_3:.2%}\n")
        f.write(f"- Average Recall@5: {summary.recall_at_5:.2%}\n")
        f.write(f"- Average Precision@1: {summary.precision_at_1:.2%}\n")
        f.write(f"- Average Precision@3: {summary.precision_at_3:.2%}\n")
        f.write(f"- Average Precision@5: {summary.precision_at_5:.2%}\n\n")

        if summary.failures:
            f.write(f"Total failures detected: {len(summary.failures)}\n\n")
        else:
            f.write("All queries achieved perfect recall at evaluated k values.\n\n")

    return json_path, md_path
