"""Tests for source-based embedding sanity checks."""

import pytest

from evaluation.embedding_sanity import (
    SanityTestCase,
    format_sanity_report,
    run_embedding_sanity_checks,
)


def test_expected_source_passes_when_it_ranks_within_top_k():
    chunks = [
        {"embedding": [1.0, 0.1], "metadata": {"source": "unrelated.md"}},
        {"embedding": [0.8, 0.6], "metadata": {"source": "expected.md"}},
    ]

    report = run_embedding_sanity_checks(
        [SanityTestCase("known query", "expected.md")],
        chunks,
        lambda _query: [1.0, 0.0],
        top_k=2,
    )

    result = report.results[0]
    assert result.passed
    assert result.top_source == "unrelated.md"
    assert result.expected_rank == 2
    assert report.passed == 1
    assert report.failed == 0


def test_missing_expected_source_is_reported_as_failure():
    report = run_embedding_sanity_checks(
        [SanityTestCase("known query", "expected.md")],
        [{"embedding": [1.0, 0.0], "source": "other.md"}],
        lambda _query: [1.0, 0.0],
    )

    formatted = format_sanity_report(report)
    assert report.failed == 1
    assert "[FAIL] known query" in formatted
    assert "expected_rank=not in top-k" in formatted


def test_empty_collection_fails_without_embedding_query():
    def unexpected_embedding(_query):
        pytest.fail("empty collection should not embed the query")

    report = run_embedding_sanity_checks(
        [SanityTestCase("known query", "expected.md")], [], unexpected_embedding
    )

    assert report.failed == 1
    assert report.results[0].top_source is None


def test_rejects_non_positive_top_k():
    with pytest.raises(ValueError, match="top_k must be greater than 0"):
        run_embedding_sanity_checks([], [], lambda _query: [1.0], top_k=0)
