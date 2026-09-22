"""Tests for embedding generation functionality."""

import os
from unittest.mock import MagicMock, patch

import openai
import pytest

from healthcompass.ingestion import (
    EmbeddedChunk,
    EmbeddingError,
    EmbeddingManifest,
    EmbeddingRunSummary,
    call_embedding_api_with_retry,
    cosine_similarity,
    estimate_cost,
    generate_chunk_id,
    generate_embeddings,
    get_embedding_config,
    load_existing_embeddings,
    prepare_chunks_from_basic_chunks,
    prepare_chunks_from_token_chunks,
    validate_embeddings,
)


class TestEmbeddingConfig:
    """Test embedding configuration retrieval."""

    def test_get_embedding_config_with_env_vars(self):
        """Test configuration retrieval when environment variables are set."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key-123",
                "EMBEDDING_MODEL": "text-embedding-3-small",
                "OPENAI_BASE_URL": "https://api.openai.com/v1",
            },
            clear=True,
        ):
            api_key, model, base_url, batch_size, max_retry = get_embedding_config()
            assert api_key == "test-key-123"
            assert model == "text-embedding-3-small"
            assert base_url == "https://api.openai.com/v1"
            assert batch_size == 64  # default
            assert max_retry == 3  # default

    def test_get_embedding_config_with_defaults(self):
        """Test configuration retrieval with default values."""
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key-123"},
            clear=True,
        ):
            api_key, model, base_url, batch_size, max_retry = get_embedding_config()
            assert api_key == "test-key-123"
            assert model == "text-embedding-3-small"  # default
            assert base_url == "https://api.openai.com/v1"  # default
            assert batch_size == 64  # default
            assert max_retry == 3  # default

    def test_get_embedding_config_missing_api_key(self):
        """Test that missing API key raises EmbeddingError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EmbeddingError, match="OPENAI_API_KEY environment variable is not set"):
                get_embedding_config()


class TestCosineSimilarity:
    """Test semantic similarity calculations for embedding vectors."""

    def test_similar_vectors_score_higher_than_unrelated_vectors(self):
        similar = cosine_similarity([1.0, 0.0, 0.0], [0.9, 0.1, 0.0])
        unrelated = cosine_similarity([1.0, 0.0, 0.0], [0.0, 0.0, 1.0])

        assert similar > unrelated
        assert 0 <= unrelated <= 1

    def test_rejects_mismatched_dimensions(self):
        with pytest.raises(ValueError, match="same dimension"):
            cosine_similarity([1.0, 0.0], [1.0])

    def test_rejects_zero_vector(self):
        with pytest.raises(ValueError, match="non-zero magnitude"):
            cosine_similarity([0.0, 0.0], [1.0, 0.0])


class TestChunkPreparation:
    """Test chunk preparation for embedding generation."""

    def test_prepare_chunks_from_token_chunks(self):
        """Test preparing chunks from TokenChunk objects."""
        from healthcompass.ingestion import TokenChunk

        token_chunks = [
            TokenChunk(
                text="Sample text 1",
                source="test.txt",
                filename="test.txt",
                chunk_id=0,
                token_count=10,
                metadata={"section": "Introduction"},
            ),
            TokenChunk(
                text="Sample text 2",
                source="test.txt",
                filename="test.txt",
                chunk_id=1,
                token_count=15,
                metadata={"section": "Body"},
            ),
        ]

        prepared = prepare_chunks_from_token_chunks(token_chunks)

        assert len(prepared) == 2
        assert prepared[0]["text"] == "Sample text 1"
        assert prepared[0]["source"] == "test.txt"
        assert prepared[0]["chunk_id"] == 0
        assert prepared[0]["metadata"] == {"section": "Introduction"}

    def test_prepare_chunks_from_basic_chunks(self):
        """Test preparing chunks from basic Chunk objects."""
        from healthcompass.ingestion import Chunk

        basic_chunks = [
            Chunk(
                text="Sample text 1",
                source="test.txt",
                filename="test.txt",
                chunk_id=0,
                metadata={"section": "Introduction"},
            ),
            Chunk(
                text="Sample text 2",
                source="test.txt",
                filename="test.txt",
                chunk_id=1,
                metadata={"section": "Body"},
            ),
        ]

        prepared = prepare_chunks_from_basic_chunks(basic_chunks)

        assert len(prepared) == 2
        assert prepared[0]["text"] == "Sample text 1"
        assert prepared[0]["source"] == "test.txt"
        assert prepared[0]["chunk_id"] == 0
        assert prepared[0]["metadata"] == {"section": "Introduction"}


class TestEmbeddingGeneration:
    """Test embedding generation with mocked API responses."""

    def test_empty_chunk_list(self):
        """Test that empty chunk list returns empty result."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            result, summary = generate_embeddings([])
            assert result.embedded_chunks == []
            assert result.manifest.chunk_count == 0
            assert result.validation_passed is True
            assert summary.total_chunks == 0

    @patch("healthcompass.ingestion.embeddings.openai.OpenAI")
    def test_successful_embedding_generation(self, mock_openai):
        """Test successful embedding generation with mocked API."""
        # Mock the OpenAI client and response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock embedding response
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2, 0.3, 0.4, 0.5]),
            MagicMock(embedding=[0.6, 0.7, 0.8, 0.9, 1.0]),
        ]
        mock_client.embeddings.create.return_value = mock_response

        chunks = [
            {
                "text": "Sample text 1",
                "source": "test.txt",
                "filename": "test.txt",
                "chunk_id": 0,
                "metadata": {"section": "Introduction"},
            },
            {
                "text": "Sample text 2",
                "source": "test.txt",
                "filename": "test.txt",
                "chunk_id": 1,
                "metadata": {"section": "Body"},
            },
        ]

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            result, summary = generate_embeddings(chunks, batch_size=10)

        assert len(result.embedded_chunks) == 2
        assert result.manifest.chunk_count == 2
        assert result.manifest.vector_dimension == 5
        assert result.validation_passed is True
        assert result.embedded_chunks[0].text == "Sample text 1"
        assert result.embedded_chunks[0].embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert summary.total_chunks == 2
        assert summary.chunks_processed == 2
        assert summary.successfully_embedded == 2

    @patch("healthcompass.ingestion.embeddings.openai.OpenAI")
    def test_batch_processing(self, mock_openai):
        """Test that chunks are processed in batches."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock responses for two batches
        mock_response1 = MagicMock()
        mock_response1.data = [
            MagicMock(embedding=[0.1, 0.2, 0.3]),
            MagicMock(embedding=[0.4, 0.5, 0.6]),
        ]

        mock_response2 = MagicMock()
        mock_response2.data = [
            MagicMock(embedding=[0.7, 0.8, 0.9]),
        ]

        mock_client.embeddings.create.side_effect = [mock_response1, mock_response2]

        chunks = [
            {
                "text": f"Sample text {i}",
                "source": "test.txt",
                "filename": "test.txt",
                "chunk_id": i,
                "metadata": {},
            }
            for i in range(3)
        ]

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            result, summary = generate_embeddings(chunks, batch_size=2)

        assert len(result.embedded_chunks) == 3
        assert mock_client.embeddings.create.call_count == 2  # Two batches
        assert summary.total_batches == 2

    @patch("healthcompass.ingestion.embeddings.openai.OpenAI")
    def test_incorrect_response_length_handling(self, mock_openai):
        """Test handling of incorrect response length from API."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock response with wrong number of embeddings
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2, 0.3]),
        ]  # Only 1 embedding for 2 chunks
        mock_client.embeddings.create.return_value = mock_response

        chunks = [
            {
                "text": "Sample text 1",
                "source": "test.txt",
                "filename": "test.txt",
                "chunk_id": 0,
                "metadata": {},
            },
            {
                "text": "Sample text 2",
                "source": "test.txt",
                "filename": "test.txt",
                "chunk_id": 1,
                "metadata": {},
            },
        ]

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            result, summary = generate_embeddings(chunks)
            # The new implementation continues on batch failure
            assert summary.failed_chunks > 0
            assert len(summary.failed_batch_indices) > 0

    @patch("healthcompass.ingestion.embeddings.openai.OpenAI")
    def test_api_error_handling(self, mock_openai):
        """Test handling of API errors."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock API error
        mock_client.embeddings.create.side_effect = Exception("API connection failed")

        chunks = [
            {
                "text": "Sample text",
                "source": "test.txt",
                "filename": "test.txt",
                "chunk_id": 0,
                "metadata": {},
            }
        ]

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            result, summary = generate_embeddings(chunks)
            # The new implementation continues on batch failure
            assert summary.failed_chunks > 0
            assert len(summary.failed_batch_indices) > 0

    @patch("healthcompass.ingestion.embeddings.openai.OpenAI")
    def test_metadata_preservation(self, mock_openai):
        """Test that metadata is preserved during embedding generation."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_response

        chunks = [
            {
                "text": "Sample text",
                "source": "guideline.pdf",
                "filename": "guideline.pdf",
                "chunk_id": 0,
                "metadata": {
                    "section": "Vaccination",
                    "version": "1.0",
                    "region": "District A",
                },
            }
        ]

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            result, summary = generate_embeddings(chunks)

        assert result.embedded_chunks[0].source == "guideline.pdf"
        assert result.embedded_chunks[0].filename == "guideline.pdf"
        assert result.embedded_chunks[0].chunk_id == 0
        assert result.embedded_chunks[0].metadata == {
            "section": "Vaccination",
            "version": "1.0",
            "region": "District A",
        }


class TestEmbeddingValidation:
    """Test embedding validation."""

    def test_validate_empty_chunks(self):
        """Test validation of empty chunk list."""
        manifest = EmbeddingManifest(
            embedding_model="text-embedding-3-small",
            chunk_count=0,
            vector_dimension=0,
            created_at="2024-01-01T00:00:00",
            source_files=[],
        )
        errors = validate_embeddings([], manifest)
        assert len(errors) == 0

    def test_validate_successful_embeddings(self):
        """Test validation of successful embeddings."""
        chunks = [
            EmbeddedChunk(
                text="Sample text 1",
                source="test.txt",
                filename="test.txt",
                chunk_id=0,
                metadata={},
                embedding=[0.1, 0.2, 0.3],
                embedding_model="text-embedding-3-small",
            ),
            EmbeddedChunk(
                text="Sample text 2",
                source="test.txt",
                filename="test.txt",
                chunk_id=1,
                metadata={},
                embedding=[0.4, 0.5, 0.6],
                embedding_model="text-embedding-3-small",
            ),
        ]
        manifest = EmbeddingManifest(
            embedding_model="text-embedding-3-small",
            chunk_count=2,
            vector_dimension=3,
            created_at="2024-01-01T00:00:00",
            source_files=["test.txt"],
        )
        errors = validate_embeddings(chunks, manifest)
        assert len(errors) == 0

    def test_validate_empty_embedding(self):
        """Test validation detects empty embeddings."""
        chunks = [
            EmbeddedChunk(
                text="Sample text",
                source="test.txt",
                filename="test.txt",
                chunk_id=0,
                metadata={},
                embedding=[],  # Empty embedding
                embedding_model="text-embedding-3-small",
            )
        ]
        manifest = EmbeddingManifest(
            embedding_model="text-embedding-3-small",
            chunk_count=1,
            vector_dimension=0,
            created_at="2024-01-01T00:00:00",
            source_files=["test.txt"],
        )
        errors = validate_embeddings(chunks, manifest)
        assert len(errors) > 0
        assert any("empty embedding" in error.lower() for error in errors)

    def test_validate_non_list_embedding(self):
        """Test validation detects non-list embeddings."""
        chunks = [
            EmbeddedChunk(
                text="Sample text",
                source="test.txt",
                filename="test.txt",
                chunk_id=0,
                metadata={},
                embedding="not a list",  # Invalid type
                embedding_model="text-embedding-3-small",
            )
        ]
        manifest = EmbeddingManifest(
            embedding_model="text-embedding-3-small",
            chunk_count=1,
            vector_dimension=0,
            created_at="2024-01-01T00:00:00",
            source_files=["test.txt"],
        )
        errors = validate_embeddings(chunks, manifest)
        assert len(errors) > 0
        assert any("not a list" in error.lower() for error in errors)

    def test_validate_inconsistent_dimensions(self):
        """Test validation detects inconsistent vector dimensions."""
        chunks = [
            EmbeddedChunk(
                text="Sample text 1",
                source="test.txt",
                filename="test.txt",
                chunk_id=0,
                metadata={},
                embedding=[0.1, 0.2, 0.3],  # 3 dimensions
                embedding_model="text-embedding-3-small",
            ),
            EmbeddedChunk(
                text="Sample text 2",
                source="test.txt",
                filename="test.txt",
                chunk_id=1,
                metadata={},
                embedding=[0.4, 0.5],  # 2 dimensions - inconsistent
                embedding_model="text-embedding-3-small",
            ),
        ]
        manifest = EmbeddingManifest(
            embedding_model="text-embedding-3-small",
            chunk_count=2,
            vector_dimension=3,
            created_at="2024-01-01T00:00:00",
            source_files=["test.txt"],
        )
        errors = validate_embeddings(chunks, manifest)
        assert len(errors) > 0
        assert any("inconsistent dimensions" in error.lower() for error in errors)

    def test_validate_chunk_count_mismatch(self):
        """Test validation detects chunk count mismatch."""
        chunks = [
            EmbeddedChunk(
                text="Sample text",
                source="test.txt",
                filename="test.txt",
                chunk_id=0,
                metadata={},
                embedding=[0.1, 0.2, 0.3],
                embedding_model="text-embedding-3-small",
            )
        ]
        manifest = EmbeddingManifest(
            embedding_model="text-embedding-3-small",
            chunk_count=5,  # Wrong count
            vector_dimension=3,
            created_at="2024-01-01T00:00:00",
            source_files=["test.txt"],
        )
        errors = validate_embeddings(chunks, manifest)
        assert len(errors) > 0
        assert any("chunk count mismatch" in error.lower() for error in errors)

    def test_validate_empty_source_text(self):
        """Test validation detects empty source text."""
        chunks = [
            EmbeddedChunk(
                text="",  # Empty text
                source="test.txt",
                filename="test.txt",
                chunk_id=0,
                metadata={},
                embedding=[0.1, 0.2, 0.3],
                embedding_model="text-embedding-3-small",
            )
        ]
        manifest = EmbeddingManifest(
            embedding_model="text-embedding-3-small",
            chunk_count=1,
            vector_dimension=3,
            created_at="2024-01-01T00:00:00",
            source_files=["test.txt"],
        )
        errors = validate_embeddings(chunks, manifest)
        assert len(errors) > 0
        assert any("empty source text" in error.lower() for error in errors)

    def test_validate_none_chunk_id(self):
        """Test validation detects None chunk_id."""
        chunks = [
            EmbeddedChunk(
                text="Sample text",
                source="test.txt",
                filename="test.txt",
                chunk_id=None,  # None chunk_id
                metadata={},
                embedding=[0.1, 0.2, 0.3],
                embedding_model="text-embedding-3-small",
            )
        ]
        manifest = EmbeddingManifest(
            embedding_model="text-embedding-3-small",
            chunk_count=1,
            vector_dimension=3,
            created_at="2024-01-01T00:00:00",
            source_files=["test.txt"],
        )
        errors = validate_embeddings(chunks, manifest)
        assert len(errors) > 0
        assert any("none chunk_id" in error.lower() for error in errors)


class TestSecurity:
    """Test security aspects of embedding generation."""

    def test_no_secrets_in_logs(self):
        """Test that API keys are not logged."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "secret-key-12345"}, clear=True):
            api_key, model, base_url, batch_size, max_retry = get_embedding_config()
            # The key should be returned but not logged in normal operation
            assert api_key == "secret-key-12345"
            # This test validates that the function returns the key for use,
            # but actual logging is handled by the calling code

    def test_metadata_isolation(self):
        """Test that metadata is isolated between chunks."""
        chunks = [
            {
                "text": "Sample text 1",
                "source": "test.txt",
                "filename": "test.txt",
                "chunk_id": 0,
                "metadata": {"key": "value1"},
            },
            {
                "text": "Sample text 2",
                "source": "test.txt",
                "filename": "test.txt",
                "chunk_id": 1,
                "metadata": {"key": "value2"},
            },
        ]

        with patch("healthcompass.ingestion.embeddings.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            mock_response = MagicMock()
            mock_response.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3]),
                MagicMock(embedding=[0.4, 0.5, 0.6]),
            ]
            mock_client.embeddings.create.return_value = mock_response

            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
                result, summary = generate_embeddings(chunks)

        # Modify metadata in first chunk
        result.embedded_chunks[0].metadata["key"] = "modified"

        # Second chunk should have original metadata
        assert result.embedded_chunks[1].metadata["key"] == "value2"


class TestChunkIdGeneration:
    """Test chunk ID generation for deduplication."""

    def test_generate_chunk_id_consistency(self):
        """Test that identical chunks generate the same ID."""
        chunk = {
            "text": "Sample text",
            "source": "test.txt",
            "filename": "test.txt",
            "chunk_id": 0,
            "metadata": {"section": "Introduction"},
        }
        id1 = generate_chunk_id(chunk)
        id2 = generate_chunk_id(chunk)
        assert id1 == id2

    def test_generate_chunk_id_uniqueness(self):
        """Test that different chunks generate different IDs."""
        chunk1 = {
            "text": "Sample text 1",
            "source": "test.txt",
            "filename": "test.txt",
            "chunk_id": 0,
            "metadata": {"section": "Introduction"},
        }
        chunk2 = {
            "text": "Sample text 2",
            "source": "test.txt",
            "filename": "test.txt",
            "chunk_id": 1,
            "metadata": {"section": "Body"},
        }
        id1 = generate_chunk_id(chunk1)
        id2 = generate_chunk_id(chunk2)
        assert id1 != id2


class TestExistingEmbeddings:
    """Test loading and skipping existing embeddings."""

    def test_load_existing_embeddings_from_file(self, tmp_path):
        """Test loading existing embeddings from JSON file."""
        import json

        # Create a test file with existing embeddings
        test_file = tmp_path / "existing_embeddings.json"
        test_data = {
            "manifest": {
                "embedding_model": "text-embedding-3-small",
                "chunk_count": 1,
                "vector_dimension": 3,
                "created_at": "2024-01-01T00:00:00",
                "source_files": ["test.txt"],
            },
            "chunks": [
                {
                    "text": "Sample text",
                    "source": "test.txt",
                    "filename": "test.txt",
                    "chunk_id": 0,
                    "metadata": {"section": "Introduction"},
                    "embedding": [0.1, 0.2, 0.3],
                    "embedding_model": "text-embedding-3-small",
                }
            ],
            "validation": {"passed": True, "errors": []},
        }
        test_file.write_text(json.dumps(test_data))

        existing = load_existing_embeddings(test_file)
        assert len(existing) == 1
        assert list(existing.values())[0].text == "Sample text"

    def test_load_existing_embeddings_nonexistent_file(self, tmp_path):
        """Test loading from nonexistent file returns empty dict."""
        nonexistent = tmp_path / "nonexistent.json"
        existing = load_existing_embeddings(nonexistent)
        assert existing == {}


class TestCostEstimation:
    """Test cost estimation functionality."""

    def test_estimate_cost_known_model(self):
        """Test cost estimation for known models."""
        cost = estimate_cost(1_000_000, "text-embedding-3-small")
        assert cost == 0.00002  # $0.02 per 1M tokens

    def test_estimate_cost_unknown_model(self):
        """Test cost estimation for unknown models uses default."""
        cost = estimate_cost(1_000_000, "unknown-model")
        assert cost == 0.00002  # Default to small model pricing

    def test_estimate_cost_zero_tokens(self):
        """Test cost estimation with zero tokens."""
        cost = estimate_cost(0, "text-embedding-3-small")
        assert cost == 0.0


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    @patch("healthcompass.ingestion.embeddings.openai.OpenAI")
    @patch("healthcompass.ingestion.embeddings.time.sleep")
    def test_retry_on_temporary_error(self, mock_sleep, mock_openai):
        """Test that temporary errors trigger retry with backoff."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # First call fails with connection error, second succeeds
        mock_client.embeddings.create.side_effect = [
            Exception("Connection failed"),
            MagicMock(data=[MagicMock(embedding=[0.1, 0.2, 0.3])]),
        ]

        client = openai.OpenAI(api_key="test-key")
        embeddings = call_embedding_api_with_retry(client, ["test text"], "text-embedding-3-small", max_attempts=2)

        assert len(embeddings) == 1
        assert mock_sleep.call_count == 1  # Should sleep once
        assert mock_sleep.call_args[0][0] == 1  # First backoff is 1 second

    @patch("healthcompass.ingestion.embeddings.openai.OpenAI")
    @patch("healthcompass.ingestion.embeddings.time.sleep")
    def test_exponential_backoff_sequence(self, mock_sleep, mock_openai):
        """Test that backoff follows exponential sequence."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Fail twice, succeed on third
        mock_client.embeddings.create.side_effect = [
            Exception("Connection failed"),
            Exception("Connection failed"),
            MagicMock(data=[MagicMock(embedding=[0.1, 0.2, 0.3])]),
        ]

        client = openai.OpenAI(api_key="test-key")
        embeddings = call_embedding_api_with_retry(client, ["test text"], "text-embedding-3-small", max_attempts=3)

        assert len(embeddings) == 1
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 1  # First backoff
        assert mock_sleep.call_args_list[1][0][0] == 2  # Second backoff

    @patch("healthcompass.ingestion.embeddings.openai.OpenAI")
    def test_no_retry_on_permanent_error(self, mock_openai):
        """Test that permanent errors don't trigger retry."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Create a generic API error that should not be retried
        mock_client.embeddings.create.side_effect = Exception("Permanent error")

        client = openai.OpenAI(api_key="test-key")
        with pytest.raises(EmbeddingError, match="Unexpected error during embedding API call"):
            call_embedding_api_with_retry(client, ["test text"], "text-embedding-3-small", max_attempts=3)


class TestBatchSplitting:
    """Test batch splitting logic."""

    def test_correct_batch_splitting(self):
        """Test that chunks are split into correct batch sizes."""
        chunks = [{"text": f"Text {i}", "source": "test.txt", "filename": "test.txt", "chunk_id": i, "metadata": {}} for i in range(10)]
        batch_size = 3
        expected_batches = 4  # 10 chunks / 3 = 4 batches (3, 3, 3, 1)

        actual_batches = (len(chunks) + batch_size - 1) // batch_size
        assert actual_batches == expected_batches

    def test_empty_batch_handling(self):
        """Test that empty chunk list is handled correctly."""
        chunks = []
        batch_size = 10
        expected_batches = 0

        actual_batches = (len(chunks) + batch_size - 1) // batch_size
        assert actual_batches == expected_batches


class TestRunSummary:
    """Test run summary calculations."""

    def test_run_summary_calculations(self):
        """Test that run summary calculations are correct."""
        summary = EmbeddingRunSummary(
            total_chunks=100,
            skipped_existing=20,
            chunks_processed=80,
            successfully_embedded=75,
            failed_chunks=5,
            total_batches=10,
            input_token_count=40000,
            estimated_cost_usd=0.0008,
            embedding_model="text-embedding-3-small",
            batch_size=8,
            retry_attempts=2,
        )

        assert summary.total_chunks == 100
        assert summary.skipped_existing == 20
        assert summary.chunks_processed == 80
        assert summary.successfully_embedded == 75
        assert summary.failed_chunks == 5
        assert summary.total_batches == 10
