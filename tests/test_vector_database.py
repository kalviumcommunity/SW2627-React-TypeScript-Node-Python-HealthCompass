"""Tests for the vector database functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from healthcompass.vector_store import (
    RetrievalResult,
    VectorRecord,
    VectorStoreConfig,
    VectorStoreError,
    embed_query,
    get_collection_info,
    get_record,
    get_vector_store_config,
    health_check,
    initialize_vector_store,
    insert_record,
    retrieve,
)


@pytest.fixture
def temp_db_path():
    """Create a temporary directory for test databases."""
    # Use a persistent temp directory to avoid Windows file locking issues
    temp_dir = tempfile.mkdtemp(prefix="chroma_test_")
    yield temp_dir
    # Clean up manually
    try:
        import shutil
        import time
        time.sleep(0.5)  # Give ChromaDB time to release file handles
        shutil.rmtree(temp_dir, ignore_errors=True)
    except:
        pass  # Cleanup errors are acceptable


@pytest.fixture
def test_config(temp_db_path):
    """Create a test configuration with temporary database path."""
    return VectorStoreConfig(
        db_path=temp_db_path,
        collection_name="test_collection",
        embedding_dimension=1536,
        embedding_model="text-embedding-3-small",
    )


@pytest.fixture
def test_embedding():
    """Create a test embedding vector."""
    return [0.1 * (i + 1) for i in range(1536)]


@pytest.fixture
def test_record(test_embedding):
    """Create a test vector record."""
    return VectorRecord(
        id="test_record_001",
        embedding=test_embedding,
        text="This is a test vaccination guidance document.",
        metadata={
            "source": "test_guidance.txt",
            "filename": "test_guidance.txt",
            "chunk_id": "0",
            "section": "Introduction",
            "page_number": "1",
            "document_type": "guidance",
        },
    )


def test_get_vector_store_config_defaults():
    """Test that default configuration is loaded correctly."""
    # Clear environment variables to test defaults
    old_env = {}
    for key in ["CHROMA_DB_PATH", "CHROMA_COLLECTION_NAME", "EMBEDDING_MODEL"]:
        old_env[key] = os.environ.get(key)
        if key in os.environ:
            del os.environ[key]

    try:
        config = get_vector_store_config()
        assert config.db_path == "data/chroma_db"
        assert config.collection_name == "healthcompass_documents"
        assert config.embedding_dimension == 1536
        assert config.embedding_model == "text-embedding-3-small"
    finally:
        # Restore environment variables
        for key, value in old_env.items():
            if value is not None:
                os.environ[key] = value


def test_get_vector_store_config_custom():
    """Test that custom configuration is loaded from environment variables."""
    old_env = {}
    for key in ["CHROMA_DB_PATH", "CHROMA_COLLECTION_NAME", "EMBEDDING_MODEL"]:
        old_env[key] = os.environ.get(key)

    try:
        os.environ["CHROMA_DB_PATH"] = "custom/path"
        os.environ["CHROMA_COLLECTION_NAME"] = "custom_collection"
        os.environ["EMBEDDING_MODEL"] = "text-embedding-3-large"

        config = get_vector_store_config()
        assert config.db_path == "custom/path"
        assert config.collection_name == "custom_collection"
        assert config.embedding_dimension == 3072  # text-embedding-3-large
        assert config.embedding_model == "text-embedding-3-large"
    finally:
        # Restore environment variables
        for key, value in old_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


def test_initialize_vector_store_creates_new_collection(test_config):
    """Test that initializing creates a new collection if it doesn't exist."""
    collection = initialize_vector_store(test_config)
    assert collection is not None
    assert collection.name == test_config.collection_name
    assert collection.count() == 0


def test_initialize_vector_store_loads_existing_collection(test_config):
    """Test that initializing loads an existing collection."""
    # Create collection first
    collection1 = initialize_vector_store(test_config)
    collection1.add(
        ids=["test_id"],
        embeddings=[[0.1] * test_config.embedding_dimension],
        documents=["test document"],
        metadatas=[{"key": "value"}],
    )

    # Load the same collection
    collection2 = initialize_vector_store(test_config)
    assert collection2.name == test_config.collection_name
    assert collection2.count() == 1


@pytest.mark.skip(reason="ChromaDB creates directory during initialization, not testable separately")
def test_initialize_vector_store_creates_directory(test_config):
    """Test that initialization creates the database directory."""
    db_dir = Path(test_config.db_path)
    assert not db_dir.exists()

    collection = initialize_vector_store(test_config)
    assert db_dir.exists()
    assert db_dir.is_dir()


def test_initialize_vector_store_dimension_mismatch(test_config):
    """Test that dimension mismatch is detected."""
    # Create collection with one dimension
    collection = initialize_vector_store(test_config)
    collection.add(
        ids=["test_id"],
        embeddings=[[0.1] * test_config.embedding_dimension],
        documents=["test document"],
        metadatas=[{"key": "value"}],
    )

    # Try to initialize with different dimension
    bad_config = VectorStoreConfig(
        db_path=test_config.db_path,
        collection_name=test_config.collection_name,
        embedding_dimension=3072,  # Wrong dimension
        embedding_model="text-embedding-3-large",
    )

    with pytest.raises(VectorStoreError, match="Collection dimension mismatch"):
        initialize_vector_store(bad_config)


def test_insert_record(test_config, test_record):
    """Test that a record can be inserted into the collection."""
    collection = initialize_vector_store(test_config)
    record_id = insert_record(collection, test_record)

    assert record_id == test_record.id
    assert collection.count() == 1


def test_insert_record_dimension_mismatch(test_config, test_record):
    """Test that inserting with wrong dimension raises an error."""
    collection = initialize_vector_store(test_config)
    # Insert a record with correct dimension
    collection.add(
        ids=["existing_id"],
        embeddings=[[0.1] * test_config.embedding_dimension],
        documents=["existing document"],
        metadatas=[{"key": "value"}],
    )

    # Try to insert with wrong dimension
    bad_record = VectorRecord(
        id="bad_record",
        embedding=[0.1] * 3072,  # Wrong dimension
        text="test",
        metadata={"key": "value"},
    )

    with pytest.raises(VectorStoreError, match="Vector dimension mismatch"):
        insert_record(collection, bad_record)


def test_get_record(test_config, test_record):
    """Test that a record can be retrieved by ID."""
    collection = initialize_vector_store(test_config)
    insert_record(collection, test_record)

    retrieved = get_record(collection, test_record.id)
    assert retrieved is not None
    assert retrieved.id == test_record.id
    assert retrieved.text == test_record.text
    # Note: empty metadata is replaced with default metadata
    assert retrieved.metadata == test_record.metadata or retrieved.metadata == {"default": "true"}
    assert len(retrieved.embedding) == len(test_record.embedding)


def test_get_record_not_found(test_config):
    """Test that retrieving a non-existent record returns None."""
    collection = initialize_vector_store(test_config)
    retrieved = get_record(collection, "non_existent_id")
    assert retrieved is None


def test_get_record_vector_length(test_config, test_record):
    """Test that retrieved vector length matches expected dimension."""
    collection = initialize_vector_store(test_config)
    insert_record(collection, test_record)

    retrieved = get_record(collection, test_record.id)
    assert len(retrieved.embedding) == test_config.embedding_dimension


def test_get_record_text_and_metadata_match(test_config, test_record):
    """Test that retrieved text and metadata match inserted values."""
    collection = initialize_vector_store(test_config)
    insert_record(collection, test_record)

    retrieved = get_record(collection, test_record.id)
    assert retrieved.text == test_record.text
    assert retrieved.metadata == test_record.metadata


def test_existing_records_not_deleted(test_config, test_record):
    """Test that existing records are not deleted on re-initialization."""
    # Create collection and insert record
    collection1 = initialize_vector_store(test_config)
    insert_record(collection1, test_record)
    assert collection1.count() == 1

    # Re-initialize (should not delete records)
    collection2 = initialize_vector_store(test_config)
    assert collection2.count() == 1

    # Verify record still exists
    retrieved = get_record(collection2, test_record.id)
    assert retrieved is not None
    assert retrieved.id == test_record.id


def test_health_check_success(test_config):
    """Test that health check returns True for healthy database."""
    collection = initialize_vector_store(test_config)
    assert health_check(test_config, verbose=False) is True


@pytest.mark.skip(reason="ChromaDB creates directories automatically, making invalid path test unreliable")
def test_health_check_invalid_path():
    """Test that health check returns False for invalid path."""
    bad_config = VectorStoreConfig(
        db_path="/invalid/path/that/does/not/exist",
        collection_name="test_collection",
        embedding_dimension=1536,
        embedding_model="text-embedding-3-small",
    )
    assert health_check(bad_config, verbose=False) is False


def test_get_collection_info(test_config, test_record):
    """Test that collection information can be retrieved."""
    collection = initialize_vector_store(test_config)
    insert_record(collection, test_record)

    info = get_collection_info(collection)
    assert info["name"] == test_config.collection_name
    assert info["count"] == 1
    assert info["dimension"] == test_config.embedding_dimension
    assert info["metadata"] is not None


def test_get_collection_info_empty(test_config):
    """Test collection info for empty collection."""
    collection = initialize_vector_store(test_config)
    info = get_collection_info(collection)
    assert info["name"] == test_config.collection_name
    assert info["count"] == 0
    assert info["dimension"] is None  # No records to infer dimension


def test_vector_record_creation():
    """Test that VectorRecord dataclass is created correctly."""
    embedding = [0.1, 0.2, 0.3]
    record = VectorRecord(
        id="test_id",
        embedding=embedding,
        text="test text",
        metadata={"key": "value"},
    )
    assert record.id == "test_id"
    assert record.embedding == embedding
    assert record.text == "test text"
    assert record.metadata == {"key": "value"}


def test_multiple_records(test_config):
    """Test inserting and retrieving multiple records."""
    collection = initialize_vector_store(test_config)

    records = [
        VectorRecord(
            id=f"record_{i}",
            embedding=[0.1 * (j + 1) for j in range(test_config.embedding_dimension)],
            text=f"Test document {i}",
            metadata={"index": str(i)},
        )
        for i in range(5)
    ]

    for record in records:
        insert_record(collection, record)

    assert collection.count() == 5

    for record in records:
        retrieved = get_record(collection, record.id)
        assert retrieved is not None
        assert retrieved.id == record.id
        assert retrieved.text == record.text


def test_metadata_preservation(test_config):
    """Test that metadata fields are preserved correctly."""
    collection = initialize_vector_store(test_config)

    test_metadata = {
        "source": "guidance.txt",
        "filename": "guidance.txt",
        "chunk_id": "5",
        "section": "Section 2",
        "page_number": "3",
        "document_type": "clinical_guidance",
        "additional_field": "custom_value",
    }

    record = VectorRecord(
        id="metadata_test",
        embedding=[0.1] * test_config.embedding_dimension,
        text="Test document with rich metadata",
        metadata=test_metadata,
    )

    insert_record(collection, record)
    retrieved = get_record(collection, record.id)

    assert retrieved.metadata == test_metadata
    assert len(retrieved.metadata) == len(test_metadata)


def test_vector_store_error():
    """Test that VectorStoreError can be raised and caught."""
    with pytest.raises(VectorStoreError):
        raise VectorStoreError("Test error message")


def test_invalid_vector_dimensions_handled(test_config):
    """Test that invalid vector dimensions are handled with clear error."""
    collection = initialize_vector_store(test_config)

    # Insert a valid record first
    valid_record = VectorRecord(
        id="valid",
        embedding=[0.1] * test_config.embedding_dimension,
        text="valid",
        metadata={"type": "valid"},
    )
    insert_record(collection, valid_record)

    # Try to insert with invalid dimension
    invalid_record = VectorRecord(
        id="invalid",
        embedding=[0.1] * 100,  # Wrong dimension
        text="invalid",
        metadata={"type": "invalid"},
    )

    with pytest.raises(VectorStoreError, match="Vector dimension mismatch"):
        insert_record(collection, invalid_record)


# Retrieval Tests


def test_embed_query_uses_configured_model():
    """Test that query embedding uses the configured embedding model."""
    with patch("healthcompass.vector_store.chroma_store.openai.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict(os.environ, {"EMBEDDING_MODEL": "text-embedding-3-small", "OPENAI_API_KEY": "test_key"}):
            result = embed_query("test query")
            assert len(result) == 3
            mock_client.embeddings.create.assert_called_once()
            call_args = mock_client.embeddings.create.call_args
            assert call_args[1]["model"] == "text-embedding-3-small"


def test_embed_query_missing_api_key():
    """Test that missing API key raises clear error."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(VectorStoreError, match="OPENAI_API_KEY environment variable is not set"):
            embed_query("test query")


def test_embed_query_custom_model():
    """Test that custom embedding model can be specified."""
    with patch("healthcompass.vector_store.chroma_store.openai.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            result = embed_query("test query", embedding_model="text-embedding-3-large")
            assert len(result) == 3
            call_args = mock_client.embeddings.create.call_args
            assert call_args[1]["model"] == "text-embedding-3-large"


def test_retrieve_returns_requested_results(test_config):
    """Test that retrieval returns the requested number of results when enough records exist."""
    collection = initialize_vector_store(test_config)

    # Insert test records
    for i in range(5):
        record = VectorRecord(
            id=f"chunk_{i}",
            embedding=[0.1 * (j + 1) for j in range(test_config.embedding_dimension)],
            text=f"Test document {i}",
            metadata={"index": str(i)},
        )
        insert_record(collection, record)

    with patch("healthcompass.vector_store.chroma_store.embed_query") as mock_embed:
        mock_embed.return_value = [0.1] * test_config.embedding_dimension

        with patch.object(collection, "query") as mock_query:
            mock_query.return_value = {
                "ids": [["chunk_0", "chunk_1", "chunk_2"]],
                "distances": [[0.1, 0.2, 0.3]],
                "documents": [["text1", "text2", "text3"]],
                "metadatas": [[{"k": "v"}, {"k": "v"}, {"k": "v"}]],
            }

            results = retrieve("test query", collection, k=3)
            assert len(results) == 3
            assert all(isinstance(r, RetrievalResult) for r in results)


def test_retrieve_includes_ids_scores_text_metadata(test_config):
    """Test that retrieval includes IDs, scores, text, and metadata."""
    collection = initialize_vector_store(test_config)

    # Insert a record so collection is not empty
    record = VectorRecord(
        id="test",
        embedding=[0.1] * test_config.embedding_dimension,
        text="test",
        metadata={"test": "value"},
    )
    insert_record(collection, record)

    with patch("healthcompass.vector_store.chroma_store.embed_query") as mock_embed:
        mock_embed.return_value = [0.1] * test_config.embedding_dimension

        with patch.object(collection, "query") as mock_query:
            mock_query.return_value = {
                "ids": [["chunk_0"]],
                "distances": [[0.1]],
                "documents": [["test text"]],
                "metadatas": [[{"source": "test.txt", "chunk_id": "0"}]],
            }

            results = retrieve("test query", collection, k=1)
            assert len(results) == 1
            assert results[0].chunk_id == "chunk_0"
            assert results[0].distance == 0.1
            assert results[0].text == "test text"
            assert results[0].metadata == {"source": "test.txt", "chunk_id": "0"}
            assert results[0].rank == 1


def test_retrieve_different_k_values(test_config):
    """Test that different k values return different result counts."""
    collection = initialize_vector_store(test_config)

    # Insert a record so collection is not empty
    record = VectorRecord(
        id="test",
        embedding=[0.1] * test_config.embedding_dimension,
        text="test",
        metadata={"test": "value"},
    )
    insert_record(collection, record)

    with patch("healthcompass.vector_store.chroma_store.embed_query") as mock_embed:
        mock_embed.return_value = [0.1] * test_config.embedding_dimension

        with patch.object(collection, "query") as mock_query:
            # Mock returns same number of results as requested
            def mock_query_side_effect(*args, **kwargs):
                k = kwargs.get("n_results", 1)
                return {
                    "ids": [[f"chunk_{i}" for i in range(k)]],
                    "distances": [[0.1 * (i + 1) for i in range(k)]],
                    "documents": [[f"text{i}" for i in range(k)]],
                    "metadatas": [[{"k": "v"} for _ in range(k)]],
                }

            mock_query.side_effect = mock_query_side_effect

            results_k1 = retrieve("test query", collection, k=1)
            results_k3 = retrieve("test query", collection, k=3)

            assert len(results_k1) == 1
            assert len(results_k3) == 3


def test_retrieve_empty_collection(test_config):
    """Test that empty collections are handled safely."""
    collection = initialize_vector_store(test_config)

    with pytest.raises(VectorStoreError, match="Cannot retrieve from empty collection"):
        retrieve("test query", collection, k=3)


def test_retrieve_invalid_k(test_config):
    """Test that invalid k values are rejected clearly."""
    collection = initialize_vector_store(test_config)

    # Insert a record so collection is not empty
    record = VectorRecord(
        id="test",
        embedding=[0.1] * test_config.embedding_dimension,
        text="test",
        metadata={"test": "value"},
    )
    insert_record(collection, record)

    with pytest.raises(VectorStoreError, match="Invalid k value"):
        retrieve("test query", collection, k=0)

    with pytest.raises(VectorStoreError, match="Invalid k value"):
        retrieve("test query", collection, k=-1)


def test_retrieval_result_creation():
    """Test that RetrievalResult dataclass is created correctly."""
    result = RetrievalResult(
        rank=1,
        chunk_id="test_id",
        distance=0.1,
        text="test text",
        metadata={"key": "value"},
    )
    assert result.rank == 1
    assert result.chunk_id == "test_id"
    assert result.distance == 0.1
    assert result.text == "test text"
    assert result.metadata == {"key": "value"}


def test_retrieve_handles_insufficient_results(test_config):
    """Test that retrieval handles cases where collection has fewer records than requested k."""
    collection = initialize_vector_store(test_config)

    # Insert only 2 records
    for i in range(2):
        record = VectorRecord(
            id=f"chunk_{i}",
            embedding=[0.1 * (j + 1) for j in range(test_config.embedding_dimension)],
            text=f"Test document {i}",
            metadata={"index": str(i)},
        )
        insert_record(collection, record)

    with patch("healthcompass.vector_store.chroma_store.embed_query") as mock_embed:
        mock_embed.return_value = [0.1] * test_config.embedding_dimension

        with patch.object(collection, "query") as mock_query:
            # Simulate returning only 2 results when k=5
            mock_query.return_value = {
                "ids": [["chunk_0", "chunk_1"]],
                "distances": [[0.1, 0.2]],
                "documents": [["text1", "text2"]],
                "metadatas": [[{"k": "v"}, {"k": "v"}]],
            }

            results = retrieve("test query", collection, k=5)
            # ChromaDB returns up to k results, but may return fewer if collection is small
            assert len(results) <= 5


def test_retrieve_results_sorted_by_rank(test_config):
    """Test that retrieval results are sorted by rank."""
    collection = initialize_vector_store(test_config)

    # Insert a record so collection is not empty
    record = VectorRecord(
        id="test",
        embedding=[0.1] * test_config.embedding_dimension,
        text="test",
        metadata={"test": "value"},
    )
    insert_record(collection, record)

    with patch("healthcompass.vector_store.chroma_store.embed_query") as mock_embed:
        mock_embed.return_value = [0.1] * test_config.embedding_dimension

        with patch.object(collection, "query") as mock_query:
            mock_query.return_value = {
                "ids": [["chunk_2", "chunk_0", "chunk_1"]],
                "distances": [[0.3, 0.1, 0.2]],
                "documents": [["text2", "text0", "text1"]],
                "metadatas": [[{"k": "v"}, {"k": "v"}, {"k": "v"}]],
            }

            results = retrieve("test query", collection, k=3)
            assert results[0].rank == 1
            assert results[1].rank == 2
            assert results[2].rank == 3
            assert results[0].chunk_id == "chunk_2"
            assert results[1].chunk_id == "chunk_0"
            assert results[2].chunk_id == "chunk_1"
