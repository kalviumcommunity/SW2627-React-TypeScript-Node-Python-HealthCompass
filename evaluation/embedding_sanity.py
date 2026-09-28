"""Quick source-based sanity checks for embedding and retrieval behavior."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from healthcompass.ingestion import EmbeddedChunk, rank_chunks_by_similarity


@dataclass(frozen=True)
class SanityTestCase:
    """A query and the source expected among its nearest chunks."""

    query: str
    expected_source: str


@dataclass(frozen=True)
class SanityCheckResult:
    """Ranking outcome for one known query."""

    query: str
    expected_source: str
    top_source: str | None
    top_score: float | None
    expected_rank: int | None
    passed: bool


@dataclass(frozen=True)
class SanityReport:
    """Results and summary counts for a group of sanity checks."""

    results: list[SanityCheckResult]
    top_k: int

    @property
    def passed(self) -> int:
        return sum(result.passed for result in self.results)

    @property
    def failed(self) -> int:
        return len(self.results) - self.passed


def run_embedding_sanity_checks(
    test_cases: Sequence[SanityTestCase],
    chunk_records: Sequence[EmbeddedChunk | Mapping[str, Any]],
    embed_query: Callable[[str], list[float]],
    top_k: int = 3,
) -> SanityReport:
    """Check whether each expected source appears in the top-k chunk ranking.

    ``embed_query`` must use the same embedding model as ``chunk_records``.
    """
    if top_k < 1:
        raise ValueError("top_k must be greater than 0")

    results = []
    for case in test_cases:
        ranked = (
            rank_chunks_by_similarity(embed_query(case.query), chunk_records, top_k)
            if chunk_records
            else []
        )
        ranked_sources = [
            str(
                record.get("source")
                or record.get("metadata", {}).get("source")
                or "unknown"
            )
            for record in ranked
        ]
        expected_rank = next(
            (
                rank
                for rank, source in enumerate(ranked_sources, start=1)
                if source == case.expected_source
            ),
            None,
        )
        results.append(
            SanityCheckResult(
                query=case.query,
                expected_source=case.expected_source,
                top_source=ranked_sources[0] if ranked_sources else None,
                top_score=float(ranked[0]["score"]) if ranked else None,
                expected_rank=expected_rank,
                passed=expected_rank is not None,
            )
        )

    return SanityReport(results=results, top_k=top_k)


def format_sanity_report(report: SanityReport) -> str:
    """Format a concise human-readable report, including failed cases."""
    lines = [
        "Embedding sanity report",
        f"tests: {len(report.results)} passed: {report.passed} failed: {report.failed}",
    ]
    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        top_score = f"{result.top_score:.4f}" if result.top_score is not None else "n/a"
        expected_rank = str(result.expected_rank) if result.expected_rank else "not in top-k"
        top_source = result.top_source or "no chunks available"
        lines.append(
            f"[{status}] {result.query} | expected={result.expected_source} "
            f"top={top_source} score={top_score} expected_rank={expected_rank}"
        )
    return "\n".join(lines)