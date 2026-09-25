"""Tests for retrieval evaluation metrics."""

from evaluation.evaluate_retrieval import (
    QueryEvaluationResult,
    QueryLabel,
    RetrievedChunk,
    calculate_precision_at_k,
    calculate_recall_at_k,
)


class TestRecallAtK:
    """Tests for Recall@k calculation."""

    def test_perfect_recall(self):
        """Test Recall@k when all relevant chunks are retrieved."""
        retrieved = ["chunk_1", "chunk_2", "chunk_3"]
        relevant = ["chunk_1", "chunk_2"]
        recall = calculate_recall_at_k(retrieved, relevant)
        assert recall == 1.0

    def test_partial_recall(self):
        """Test Recall@k when only some relevant chunks are retrieved."""
        retrieved = ["chunk_1", "chunk_3", "chunk_4"]
        relevant = ["chunk_1", "chunk_2"]
        recall = calculate_recall_at_k(retrieved, relevant)
        assert recall == 0.5

    def test_zero_recall(self):
        """Test Recall@k when no relevant chunks are retrieved."""
        retrieved = ["chunk_3", "chunk_4"]
        relevant = ["chunk_1", "chunk_2"]
        recall = calculate_recall_at_k(retrieved, relevant)
        assert recall == 0.0

    def test_empty_relevant(self):
        """Test Recall@k when there are no relevant chunks."""
        retrieved = ["chunk_1", "chunk_2"]
        relevant = []
        recall = calculate_recall_at_k(retrieved, relevant)
        assert recall == 0.0

    def test_empty_retrieved(self):
        """Test Recall@k when no chunks are retrieved."""
        retrieved = []
        relevant = ["chunk_1", "chunk_2"]
        recall = calculate_recall_at_k(retrieved, relevant)
        assert recall == 0.0

    def test_duplicate_retrieved_ids(self):
        """Test Recall@k handles duplicate retrieved IDs correctly."""
        retrieved = ["chunk_1", "chunk_1", "chunk_2"]
        relevant = ["chunk_1", "chunk_2"]
        recall = calculate_recall_at_k(retrieved, relevant)
        assert recall == 1.0


class TestPrecisionAtK:
    """Tests for Precision@k calculation."""

    def test_perfect_precision(self):
        """Test Precision@k when all retrieved chunks are relevant."""
        retrieved = ["chunk_1", "chunk_2"]
        relevant = ["chunk_1", "chunk_2"]
        precision = calculate_precision_at_k(retrieved, relevant)
        assert precision == 1.0

    def test_partial_precision(self):
        """Test Precision@k when only some retrieved chunks are relevant."""
        retrieved = ["chunk_1", "chunk_3", "chunk_4"]
        relevant = ["chunk_1", "chunk_2"]
        precision = calculate_precision_at_k(retrieved, relevant)
        assert precision == 1.0 / 3.0

    def test_zero_precision(self):
        """Test Precision@k when no retrieved chunks are relevant."""
        retrieved = ["chunk_3", "chunk_4"]
        relevant = ["chunk_1", "chunk_2"]
        precision = calculate_precision_at_k(retrieved, relevant)
        assert precision == 0.0

    def test_empty_retrieved(self):
        """Test Precision@k when no chunks are retrieved."""
        retrieved = []
        relevant = ["chunk_1", "chunk_2"]
        precision = calculate_precision_at_k(retrieved, relevant)
        assert precision == 0.0

    def test_empty_relevant(self):
        """Test Precision@k when there are no relevant chunks."""
        retrieved = ["chunk_1", "chunk_2"]
        relevant = []
        precision = calculate_precision_at_k(retrieved, relevant)
        assert precision == 0.0

    def test_duplicate_retrieved_ids(self):
        """Test Precision@k handles duplicate retrieved IDs correctly."""
        retrieved = ["chunk_1", "chunk_1", "chunk_2"]
        relevant = ["chunk_1"]
        precision = calculate_precision_at_k(retrieved, relevant)
        # Implementation uses set() for intersection but list length for denominator
        # relevant_retrieved = len(set(retrieved) & set(relevant)) = len({"chunk_1"}) = 1
        # precision = 1 / len(retrieved) = 1 / 3 = 0.333...
        # This is correct behavior - duplicates in retrieval reduce precision
        assert precision == 1.0 / 3.0


class TestMultipleRelevantChunks:
    """Tests for queries with multiple relevant chunks."""

    def test_recall_with_multiple_relevant(self):
        """Test Recall@k with multiple relevant chunks."""
        retrieved = ["chunk_1", "chunk_2", "chunk_5"]
        relevant = ["chunk_1", "chunk_2", "chunk_3", "chunk_4"]
        recall = calculate_recall_at_k(retrieved, relevant)
        assert recall == 0.5

    def test_precision_with_multiple_relevant(self):
        """Test Precision@k with multiple relevant chunks."""
        retrieved = ["chunk_1", "chunk_2", "chunk_5"]
        relevant = ["chunk_1", "chunk_2", "chunk_3", "chunk_4"]
        precision = calculate_precision_at_k(retrieved, relevant)
        assert precision == 2.0 / 3.0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_k_larger_than_available_results(self):
        """Test when k is larger than available results."""
        retrieved = ["chunk_1"]
        relevant = ["chunk_1", "chunk_2"]
        recall = calculate_recall_at_k(retrieved, relevant)
        precision = calculate_precision_at_k(retrieved, relevant)
        assert recall == 0.5
        assert precision == 1.0

    def test_single_relevant_chunk(self):
        """Test with a single relevant chunk."""
        retrieved = ["chunk_1", "chunk_2", "chunk_3"]
        relevant = ["chunk_1"]
        recall = calculate_recall_at_k(retrieved, relevant)
        precision = calculate_precision_at_k(retrieved, relevant)
        assert recall == 1.0
        assert precision == 1.0 / 3.0

    def test_all_chunks_relevant(self):
        """Test when all retrieved chunks are relevant."""
        retrieved = ["chunk_1", "chunk_2", "chunk_3"]
        relevant = ["chunk_1", "chunk_2", "chunk_3"]
        recall = calculate_recall_at_k(retrieved, relevant)
        precision = calculate_precision_at_k(retrieved, relevant)
        assert recall == 1.0
        assert precision == 1.0


class TestQueryLabel:
    """Tests for QueryLabel dataclass."""

    def test_query_label_creation(self):
        """Test creating a QueryLabel."""
        label = QueryLabel(
            query="test query",
            relevant_chunk_ids=["chunk_1", "chunk_2"],
            relevant_source="test.txt",
            explanation="test explanation",
            expected_topic="test topic",
        )
        assert label.query == "test query"
        assert label.relevant_chunk_ids == ["chunk_1", "chunk_2"]
        assert label.relevant_source == "test.txt"
        assert label.explanation == "test explanation"
        assert label.expected_topic == "test topic"

    def test_query_label_optional_fields(self):
        """Test QueryLabel with optional fields omitted."""
        label = QueryLabel(
            query="test query", relevant_chunk_ids=["chunk_1"]
        )
        assert label.query == "test query"
        assert label.relevant_chunk_ids == ["chunk_1"]
        assert label.relevant_source is None
        assert label.explanation is None
        assert label.expected_topic is None


class TestRetrievedChunk:
    """Tests for RetrievedChunk dataclass."""

    def test_retrieved_chunk_creation(self):
        """Test creating a RetrievedChunk."""
        chunk = RetrievedChunk(
            chunk_id="chunk_1",
            text="test text",
            source="test.txt",
            distance=0.5,
            is_relevant=True,
            rank=1,
        )
        assert chunk.chunk_id == "chunk_1"
        assert chunk.text == "test text"
        assert chunk.source == "test.txt"
        assert chunk.distance == 0.5
        assert chunk.is_relevant is True
        assert chunk.rank == 1


class TestQueryEvaluationResult:
    """Tests for QueryEvaluationResult dataclass."""

    def test_query_evaluation_result_creation(self):
        """Test creating a QueryEvaluationResult."""
        result = QueryEvaluationResult(
            query="test query",
            relevant_chunk_ids=["chunk_1"],
            k=3,
            retrieved_chunks=[],
            recall_at_k=1.0,
            precision_at_k=0.5,
            relevant_retrieved=1,
            total_relevant=1,
            total_retrieved=2,
        )
        assert result.query == "test query"
        assert result.relevant_chunk_ids == ["chunk_1"]
        assert result.k == 3
        assert result.recall_at_k == 1.0
        assert result.precision_at_k == 0.5
        assert result.relevant_retrieved == 1
        assert result.total_relevant == 1
        assert result.total_retrieved == 2
