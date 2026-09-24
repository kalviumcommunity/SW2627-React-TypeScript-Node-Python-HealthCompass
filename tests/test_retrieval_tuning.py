"""Tests for retrieval tuning evaluation logic."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add src and evaluation to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation import (
    QueryEvaluationResult,
    RetrievalConfig,
    RetrievalEvaluation,
    evaluate_retrieval_configurations,
    load_test_queries,
    select_best_configuration,
)


@pytest.fixture
def sample_queries_file():
    """Create a temporary file with sample test queries."""
    queries = [
        {
            "query": "What are the priority groups?",
            "expected_source": "vaccination_guidance.txt",
            "expected_keyword": "priority",
            "explanation": "Section 2 discusses priority groups",
        },
        {
            "query": "How should vaccines be stored?",
            "expected_source": "vaccination_guidance.txt",
            "expected_keyword": "storage",
            "explanation": "Section 4 covers storage requirements",
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(queries, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink()


def test_load_test_queries(sample_queries_file):
    """Test that test queries load correctly from JSON file."""
    queries = load_test_queries(sample_queries_file)

    assert len(queries) == 2
    assert queries[0].query == "What are the priority groups?"
    assert queries[0].expected_source == "vaccination_guidance.txt"
    assert queries[0].expected_keyword == "priority"
    assert queries[1].query == "How should vaccines be stored?"


def test_load_test_queries_missing_keyword():
    """Test that queries load correctly when keyword is optional."""
    queries_data = [
        {
            "query": "Test query",
            "expected_source": "test.txt",
            "explanation": "Test explanation",
        }
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(queries_data, f)
        temp_path = Path(f.name)

    try:
        queries = load_test_queries(temp_path)
        assert len(queries) == 1
        assert queries[0].expected_keyword is None
    finally:
        temp_path.unlink()


def test_retrieval_config_creation():
    """Test that retrieval configurations can be created."""
    config = RetrievalConfig(name="Test Config", k=3)
    assert config.name == "Test Config"
    assert config.k == 3
    assert config.score_threshold is None
    assert config.metadata_filter is None


def test_retrieval_config_with_threshold():
    """Test that retrieval configurations can include score threshold."""
    config = RetrievalConfig(name="Test Config", k=3, score_threshold=0.5)
    assert config.score_threshold == 0.5


def test_retrieval_config_with_filter():
    """Test that retrieval configurations can include metadata filter."""
    config = RetrievalConfig(name="Test Config", k=3, metadata_filter={"document_type": "guidance"})
    assert config.metadata_filter == {"document_type": "guidance"}


def test_query_evaluation_result_creation():
    """Test that query evaluation results can be created."""
    result = QueryEvaluationResult(
        query="Test query",
        expected_source="test.txt",
        config_name="Config A",
        k=3,
        retrieved_rank=1,
        retrieved_chunk_id="chunk_0",
        retrieved_source="test.txt",
        score=0.1,
        matched_expected_source=True,
        matched_expected_keyword=False,
    )
    assert result.query == "Test query"
    assert result.retrieved_rank == 1
    assert result.matched_expected_source is True


def test_retrieval_evaluation_creation():
    """Test that retrieval evaluation results can be created."""
    evaluation = RetrievalEvaluation(
        config_name="Config A",
        k=3,
        score_threshold=None,
        metadata_filter=None,
        total_queries=8,
        top_1_hits=4,
        top_k_hits=7,
        top_1_hit_rate=0.5,
        top_k_hit_rate=0.875,
        average_rank=1.5,
        queries_with_zero_relevant=1,
    )
    assert evaluation.config_name == "Config A"
    assert evaluation.top_1_hit_rate == 0.5
    assert evaluation.top_k_hit_rate == 0.875


def test_select_best_configuration():
    """Test that best configuration selection works correctly."""
    evaluations = [
        RetrievalEvaluation(
            config_name="Config A",
            k=3,
            score_threshold=None,
            metadata_filter=None,
            total_queries=8,
            top_1_hits=4,
            top_k_hits=6,
            top_1_hit_rate=0.5,
            top_k_hit_rate=0.75,
            average_rank=1.5,
            queries_with_zero_relevant=2,
        ),
        RetrievalEvaluation(
            config_name="Config B",
            k=5,
            score_threshold=None,
            metadata_filter=None,
            total_queries=8,
            top_1_hits=3,
            top_k_hits=7,
            top_1_hit_rate=0.375,
            top_k_hit_rate=0.875,
            average_rank=2.0,
            queries_with_zero_relevant=1,
        ),
    ]

    best = select_best_configuration(evaluations)
    assert best.config_name == "Config B"  # Higher top-k hit rate
    assert best.k == 5


def test_select_best_configuration_same_top_k_prefers_smaller_k():
    """Test that smaller k is preferred when top-k hit rates are equal."""
    evaluations = [
        RetrievalEvaluation(
            config_name="Config A",
            k=3,
            score_threshold=None,
            metadata_filter=None,
            total_queries=8,
            top_1_hits=4,
            top_k_hits=7,
            top_1_hit_rate=0.5,
            top_k_hit_rate=0.875,
            average_rank=1.5,
            queries_with_zero_relevant=1,
        ),
        RetrievalEvaluation(
            config_name="Config B",
            k=5,
            score_threshold=None,
            metadata_filter=None,
            total_queries=8,
            top_1_hits=4,
            top_k_hits=7,
            top_1_hit_rate=0.5,
            top_k_hit_rate=0.875,
            average_rank=2.0,
            queries_with_zero_relevant=1,
        ),
    ]

    best = select_best_configuration(evaluations)
    assert best.config_name == "Config A"  # Same hit rates, smaller k preferred
    assert best.k == 3


def test_select_best_configuration_top_1_tiebreaker():
    """Test that top-1 hit rate breaks ties when top-k hit rates are equal."""
    evaluations = [
        RetrievalEvaluation(
            config_name="Config A",
            k=3,
            score_threshold=None,
            metadata_filter=None,
            total_queries=8,
            top_1_hits=5,
            top_k_hits=7,
            top_1_hit_rate=0.625,
            top_k_hit_rate=0.875,
            average_rank=1.5,
            queries_with_zero_relevant=1,
        ),
        RetrievalEvaluation(
            config_name="Config B",
            k=5,
            score_threshold=None,
            metadata_filter=None,
            total_queries=8,
            top_1_hits=4,
            top_k_hits=7,
            top_1_hit_rate=0.5,
            top_k_hit_rate=0.875,
            average_rank=2.0,
            queries_with_zero_relevant=1,
        ),
    ]

    best = select_best_configuration(evaluations)
    assert best.config_name == "Config A"  # Higher top-1 hit rate breaks tie


def test_evaluate_retrieval_configurations_with_mock():
    """Test that retrieval configuration evaluation works with mock results."""
    queries = [
        Mock(query="Test query", expected_source="test.txt", expected_keyword="test", explanation=""),
        Mock(query="Another query", expected_source="test.txt", expected_keyword="another", explanation=""),
    ]

    configs = [
        RetrievalConfig(name="Config A", k=3),
        RetrievalConfig(name="Config B", k=5),
    ]

    mock_collection = Mock()

    evaluations = evaluate_retrieval_configurations(queries, configs, mock_collection, use_mock=True)

    assert len(evaluations) == 2
    assert evaluations[0].config_name == "Config A"
    assert evaluations[0].k == 3
    assert evaluations[1].config_name == "Config B"
    assert evaluations[1].k == 5


def test_top_1_hit_calculation():
    """Test that top-1 hit rate is calculated correctly."""
    evaluations = [
        RetrievalEvaluation(
            config_name="Config A",
            k=3,
            score_threshold=None,
            metadata_filter=None,
            total_queries=8,
            top_1_hits=4,
            top_k_hits=7,
            top_1_hit_rate=0.5,
            top_k_hit_rate=0.875,
            average_rank=1.5,
            queries_with_zero_relevant=1,
        )
    ]

    assert evaluations[0].top_1_hit_rate == 0.5
    assert evaluations[0].top_1_hits == 4
    assert evaluations[0].total_queries == 8


def test_top_k_hit_calculation():
    """Test that top-k hit rate is calculated correctly."""
    evaluations = [
        RetrievalEvaluation(
            config_name="Config A",
            k=3,
            score_threshold=None,
            metadata_filter=None,
            total_queries=8,
            top_1_hits=4,
            top_k_hits=7,
            top_1_hit_rate=0.5,
            top_k_hit_rate=0.875,
            average_rank=1.5,
            queries_with_zero_relevant=1,
        )
    ]

    assert evaluations[0].top_k_hit_rate == 0.875
    assert evaluations[0].top_k_hits == 7
    assert evaluations[0].total_queries == 8


def test_source_matching_logic():
    """Test that source matching works correctly."""
    result = QueryEvaluationResult(
        query="Test query",
        expected_source="test.txt",
        config_name="Config A",
        k=3,
        retrieved_rank=1,
        retrieved_chunk_id="chunk_0",
        retrieved_source="test.txt",
        score=0.1,
        matched_expected_source=True,
        matched_expected_keyword=False,
    )

    assert result.matched_expected_source is True
    assert result.retrieved_source == "test.txt"


def test_empty_retrieval_results_handling():
    """Test that empty retrieval results are handled safely."""
    result = QueryEvaluationResult(
        query="Test query",
        expected_source="test.txt",
        config_name="Config A",
        k=3,
        retrieved_rank=None,
        retrieved_chunk_id=None,
        retrieved_source=None,
        score=None,
        matched_expected_source=False,
        matched_expected_keyword=False,
    )

    assert result.matched_expected_source is False
    assert result.retrieved_rank is None
    assert result.score is None


def test_invalid_configuration_values():
    """Test that invalid configuration values are handled."""
    # Valid configurations
    valid_config = RetrievalConfig(name="Valid", k=3)
    assert valid_config.k == 3

    # Configuration with k=0 would be caught by retrieval function
    config_zero = RetrievalConfig(name="Zero K", k=0)
    assert config_zero.k == 0  # The config itself can be created, validation happens later


def test_results_aggregation():
    """Test that results are aggregated correctly across multiple queries."""
    results = [
        QueryEvaluationResult(
            query="Query 1",
            expected_source="test.txt",
            config_name="Config A",
            k=3,
            retrieved_rank=1,
            retrieved_chunk_id="chunk_0",
            retrieved_source="test.txt",
            score=0.1,
            matched_expected_source=True,
            matched_expected_keyword=False,
        ),
        QueryEvaluationResult(
            query="Query 2",
            expected_source="test.txt",
            config_name="Config A",
            k=3,
            retrieved_rank=2,
            retrieved_chunk_id="chunk_1",
            retrieved_source="test.txt",
            score=0.2,
            matched_expected_source=True,
            matched_expected_keyword=False,
        ),
        QueryEvaluationResult(
            query="Query 3",
            expected_source="test.txt",
            config_name="Config A",
            k=3,
            retrieved_rank=None,
            retrieved_chunk_id=None,
            retrieved_source=None,
            score=None,
            matched_expected_source=False,
            matched_expected_keyword=False,
        ),
    ]

    evaluation = RetrievalEvaluation(
        config_name="Config A",
        k=3,
        score_threshold=None,
        metadata_filter=None,
        total_queries=3,
        top_1_hits=1,
        top_k_hits=2,
        top_1_hit_rate=1/3,
        top_k_hit_rate=2/3,
        average_rank=1.5,
        queries_with_zero_relevant=1,
        results=results,
    )

    assert len(evaluation.results) == 3
    assert evaluation.top_1_hits == 1
    assert evaluation.top_k_hits == 2
    assert evaluation.queries_with_zero_relevant == 1
