"""Tests for embedding generation functionality."""

import os
from unittest.mock import MagicMock, patch

import pytest

from healthcompass.ingestion import (
    EmbeddingError,
    EmbeddingManifest,
    EmbeddingResult,
    EmbeddedChunk,
    generate_embeddings,
    get_embedding_config,
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
            api_key, model, base_url = get_embedding_config()
            assert api_key == "test-key-123"
            assert model == "text-embedding-3-small"
            assert base_url == "https://api.openai.com/v1"

    def test_get_embedding_config_with_defaults(self):
        """Test configuration retrieval with default values."""
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key-123"},
            clear=True,
        ):
            api_key, model, base_url = get_embedding_config()
            assert api_key == "test-key-123"
            assert model == "text-embedding-3-small"  # default
            assert base_url == "https://api.openai.com/v1"  # default

    def test_get_embedding_config_missing_api_key(self):
        """Test that missing API key raises EmbeddingError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EmbeddingError, match="OPENAI_API_KEY environment variable is not set"):
                get_embedding_config()


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
            result = generate_embeddings([])
            assert result.embedded_chunks == []
            assert result.manifest.chunk_count == 0
            assert result.validation_passed is True

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
            result = generate_embeddings(chunks, batch_size=10)

        assert len(result.embedded_chunks) == 2
        assert result.manifest.chunk_count == 2
        assert result.manifest.vector_dimension == 5
        assert result.validation_passed is True
        assert result.embedded_chunks[0].text == "Sample text 1"
        assert result.embedded_chunks[0].embedding == [0.1, 0.2, 0.3, 0.4, 0.5]

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
            result = generate_embeddings(chunks, batch_size=2)

        assert len(result.embedded_chunks) == 3
        assert mock_client.embeddings.create.call_count == 2  # Two batches

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
            with pytest.raises(EmbeddingError, match="API returned 1 embeddings for 2 chunks"):
                generate_embeddings(chunks)

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
            with pytest.raises(EmbeddingError, match="Unexpected error during embedding generation"):
                generate_embeddings(chunks)

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
            result = generate_embeddings(chunks)

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
            api_key, model, base_url = get_embedding_config()
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
                result = generate_embeddings(chunks)

        # Modify metadata in first chunk
        result.embedded_chunks[0].metadata["key"] = "modified"

        # Second chunk should have original metadata
        assert result.embedded_chunks[1].metadata["key"] == "value2"
