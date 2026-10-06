"""ChromaDB vector store for HealthCompass RAG system."""

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
import openai
from chromadb.config import Settings
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


@dataclass
class VectorStoreConfig:
    """Configuration for the vector database."""

    db_path: str
    collection_name: str
    embedding_dimension: int
    embedding_model: str


@dataclass
class VectorRecord:
    """A record stored in the vector database."""

    id: str
    embedding: List[float]
    text: str
    metadata: Dict[str, Any]


@dataclass
class BatchUpsertResult:
    """Outcome of a batched vector-record upsert."""

    expected_count: int
    upserted_count: int
    indexed_count: int
    failures: List[Dict[str, str]]


@dataclass
class RetrievalResult:
    """A result from similarity search retrieval."""

    rank: int
    chunk_id: str
    distance: float
    text: str
    metadata: Dict[str, Any]
    hybrid_score: float | None = None


class VectorStoreError(Exception):
    """Custom exception for vector store operations."""

    pass


def get_vector_store_config() -> VectorStoreConfig:
    """Get vector store configuration from environment variables.

    Returns:
        VectorStoreConfig with database path, collection name, and dimension

    Raises:
        VectorStoreError: If configuration is invalid
    """
    db_path = os.getenv("CHROMA_DB_PATH", "data/chroma_db")
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "healthcompass_documents")
    default_model = (
        "text-embedding-004"
        if os.getenv("GEMINI_API_KEY") and not os.getenv("OPENAI_API_KEY")
        else "text-embedding-3-small"
    )
    embedding_model = os.getenv("EMBEDDING_MODEL") or default_model

    # Vector dimensions for common embedding models
    embedding_dimensions = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
        "text-embedding-004": 768,
    }

    vector_dimension = embedding_dimensions.get(
        embedding_model, 768 if "004" in embedding_model else 1536
    )

    return VectorStoreConfig(
        db_path=db_path,
        collection_name=collection_name,
        embedding_dimension=vector_dimension,
        embedding_model=embedding_model,
    )


def initialize_vector_store(
    config: Optional[VectorStoreConfig] = None,
) -> chromadb.Collection:
    """Initialize the vector database and create or load the collection.

    Args:
        config: Optional VectorStoreConfig, uses environment variables if not provided

    Returns:
        ChromaDB Collection instance

    Raises:
        VectorStoreError: If initialization fails
    """
    if config is None:
        config = get_vector_store_config()

    try:
        # Create database directory if it doesn't exist
        db_dir = Path(config.db_path)
        db_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistent storage
        client = chromadb.PersistentClient(
            path=config.db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection
        try:
            collection = client.get_collection(name=config.collection_name)
            print(f"Loaded existing collection: {config.collection_name}")
        except (chromadb.errors.NotFoundError, chromadb.errors.InvalidCollectionException):
            collection = client.create_collection(
                name=config.collection_name,
                metadata={
                    "embedding_dimension": config.embedding_dimension,
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 200,
                    "hnsw:M": 16,
                },
            )
            print(f"Created new collection: {config.collection_name}")

        collection_metadata = collection.metadata or {}
        stored_dimension = collection_metadata.get("embedding_dimension")
        if stored_dimension is not None and stored_dimension != config.embedding_dimension:
            raise VectorStoreError(
                f"Collection dimension mismatch: expected {config.embedding_dimension}, "
                f"found {stored_dimension}. Consider recreating the collection."
            )

        # Verify collection dimension matches expected
        if collection.count() > 0:
            # Get a sample record to verify dimension
            sample = collection.get(limit=1, include=["embeddings"])
            if len(sample["embeddings"]) > 0:
                actual_dimension = len(sample["embeddings"][0])
                if actual_dimension != config.embedding_dimension:
                    raise VectorStoreError(
                        f"Collection dimension mismatch: expected {config.embedding_dimension}, "
                        f"found {actual_dimension}. Consider recreating the collection."
                    )

        if stored_dimension is None:
            collection.modify(
                metadata={
                    **collection_metadata,
                    "embedding_dimension": config.embedding_dimension,
                }
            )

        print(f"Vector database initialized at: {config.db_path}")
        print(f"Collection: {config.collection_name}")
        print(f"Embedding dimension: {config.embedding_dimension}")
        print(f"Embedding model: {config.embedding_model}")

        return collection

    except Exception as e:
        raise VectorStoreError(f"Failed to initialize vector store: {e}") from e


def insert_record(
    collection: chromadb.Collection,
    record: VectorRecord,
) -> str:
    """Insert a record into the vector database.

    Args:
        collection: ChromaDB Collection instance
        record: VectorRecord to insert

    Returns:
        The record ID

    Raises:
        VectorStoreError: If insertion fails
    """
    try:
        # Validate against the configured dimension, including on an empty collection.
        expected_dimension = (collection.metadata or {}).get("embedding_dimension")
        if expected_dimension is None:
            collection_data = collection.get(limit=1, include=["embeddings"])
            if len(collection_data["embeddings"]) > 0:
                expected_dimension = len(collection_data["embeddings"][0])

        if expected_dimension is not None and len(record.embedding) != expected_dimension:
            raise VectorStoreError(
                f"Vector dimension mismatch: expected {expected_dimension}, "
                f"got {len(record.embedding)}"
            )

        # ChromaDB requires non-empty metadata, so provide a default if empty
        metadata = record.metadata if record.metadata else {"default": "true"}

        # Insert the record
        collection.add(
            ids=[record.id],
            embeddings=[record.embedding],
            documents=[record.text],
            metadatas=[metadata],
        )

        return record.id

    except Exception as e:
        raise VectorStoreError(f"Failed to insert record: {e}") from e


def upsert_records(
    collection: chromadb.Collection,
    records: List[VectorRecord],
    batch_size: int = 100,
) -> BatchUpsertResult:
    """Upsert vector records in batches and report indexing integrity details.

    Existing IDs are replaced, so repeating an indexing run does not create
    duplicate records. Failed batches are reported while later batches continue.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be greater than 0")

    expected_dimension = (collection.metadata or {}).get("embedding_dimension")
    if expected_dimension is None:
        collection_data = collection.get(limit=1, include=["embeddings"])
        if len(collection_data["embeddings"]) > 0:
            expected_dimension = len(collection_data["embeddings"][0])

    expected_count = len(records)
    upserted_count = 0
    failures = []

    for start in range(0, expected_count, batch_size):
        batch = records[start : start + batch_size]
        try:
            for record in batch:
                if expected_dimension is not None and len(record.embedding) != expected_dimension:
                    raise VectorStoreError(
                        f"Vector dimension mismatch: expected {expected_dimension}, "
                        f"got {len(record.embedding)}"
                    )

            collection.upsert(
                ids=[record.id for record in batch],
                embeddings=[record.embedding for record in batch],
                documents=[record.text for record in batch],
                metadatas=[
                    {key: value for key, value in record.metadata.items() if value is not None}
                    or {"default": "true"}
                    for record in batch
                ],
            )
            upserted_count += len(batch)
        except Exception as error:
            failures.append({"batch_start_id": batch[0].id, "error": str(error)})

    return BatchUpsertResult(
        expected_count=expected_count,
        upserted_count=upserted_count,
        indexed_count=collection.count(),
        failures=failures,
    )


def get_record(
    collection: chromadb.Collection,
    record_id: str,
) -> Optional[VectorRecord]:
    """Retrieve a record by ID from the vector database.

    Args:
        collection: ChromaDB Collection instance
        record_id: The ID of the record to retrieve

    Returns:
        VectorRecord if found, None otherwise

    Raises:
        VectorStoreError: If retrieval fails
    """
    try:
        result = collection.get(ids=[record_id], include=["embeddings", "documents", "metadatas"])

        if not result["ids"]:
            return None

        return VectorRecord(
            id=result["ids"][0],
            embedding=result["embeddings"][0],
            text=result["documents"][0],
            metadata=result["metadatas"][0],
        )

    except Exception as e:
        raise VectorStoreError(f"Failed to retrieve record: {e}") from e


def health_check(config: Optional[VectorStoreConfig] = None, verbose: bool = True) -> bool:
    """Perform a health check on the vector database.

    Args:
        config: Optional VectorStoreConfig, uses environment variables if not provided
        verbose: Whether to print health check messages (default: True)

    Returns:
        True if health check passes, False otherwise
    """
    try:
        collection = initialize_vector_store(config)
        if verbose:
            print("Health check: Vector database is accessible")
            print(f"Collection '{collection.name}' is ready")
        return True
    except VectorStoreError as e:
        if verbose:
            print(f"Health check failed: {e}")
        return False
    except Exception as e:
        if verbose:
            print(f"Health check failed with unexpected error: {e}")
        return False


def get_collection_info(collection: chromadb.Collection) -> Dict[str, Any]:
    """Get information about the collection.

    Args:
        collection: ChromaDB Collection instance

    Returns:
        Dictionary with collection information
    """
    try:
        count = collection.count()
        sample = collection.get(limit=1, include=["embeddings"]) if count > 0 else None

        dimension = None
        if sample and len(sample["embeddings"]) > 0:
            dimension = len(sample["embeddings"][0])

        return {
            "name": collection.name,
            "count": count,
            "dimension": dimension,
            "metadata": collection.metadata,
        }
    except Exception as e:
        raise VectorStoreError(f"Failed to get collection info: {e}") from e


def embed_query(query: str, embedding_model: str | None = None) -> List[float]:
    """Embed a user query using the same embedding model as document chunks.

    Args:
        query: The user query text to embed
        embedding_model: Optional embedding model name, uses environment variable if not provided

    Returns:
        The embedding vector for the query

    Raises:
        VectorStoreError: If embedding generation fails
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if gemini_key:
        api_key = gemini_key
        base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
        default_model = "text-embedding-004"
    elif openai_key:
        api_key = openai_key
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        default_model = "text-embedding-3-small"
    else:
        raise VectorStoreError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please configure your API key (OPENAI_API_KEY or GEMINI_API_KEY) in .env file or environment variables."
        )

    if embedding_model is None:
        embedding_model = os.getenv("EMBEDDING_MODEL", default_model)

    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.embeddings.create(input=[query], model=embedding_model)
        return response.data[0].embedding
    except openai.RateLimitError as e:
        raise VectorStoreError(f"Rate limit error during query embedding: {e}") from e
    except openai.APIError as e:
        raise VectorStoreError(f"API error during query embedding: {e}") from e
    except Exception as e:
        raise VectorStoreError(f"Failed to embed query: {e}") from e


def retrieve(
    query: str,
    collection: chromadb.Collection,
    k: int = 3,
    embedding_model: str | None = None,
    metadata_filter: Mapping[str, Any] | None = None,
    keyword_weight: float = 0.0,
) -> List[RetrievalResult]:
    """Perform top-k similarity search for a query against the vector database.

    Args:
        query: The user query text
        collection: ChromaDB Collection instance
        k: Number of results to retrieve (default: 3)
        embedding_model: Optional embedding model name, uses environment variable if not provided
        metadata_filter: Optional Chroma ``where`` filter.
        keyword_weight: Blend factor from 0 (semantic only) to 1 (keyword only).

    Returns:
        List of RetrievalResult objects ranked by similarity

    Raises:
        VectorStoreError: If retrieval fails or k is invalid
    """
    if k <= 0:
        raise VectorStoreError(f"Invalid k value: {k}. k must be greater than 0.")
    if not 0.0 <= keyword_weight <= 1.0:
        raise VectorStoreError("keyword_weight must be between 0 and 1.")
    if metadata_filter is not None and not isinstance(metadata_filter, Mapping):
        raise VectorStoreError(
            "metadata_filter must be a mapping compatible with Chroma where filters."
        )

    collection_count = collection.count()
    if collection_count == 0:
        raise VectorStoreError("Cannot retrieve from empty collection.")

    try:
        # Embed the query
        query_embedding = embed_query(query, embedding_model)

        candidate_count = min(collection_count, max(k, k * 3)) if keyword_weight else k
        query_options: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": candidate_count,
            "include": ["documents", "metadatas", "distances"],
        }
        if metadata_filter:
            query_options["where"] = dict(metadata_filter)
        results = collection.query(**query_options)
        records = [
            {
                "chunk_id": results["ids"][0][index],
                "distance": results["distances"][0][index],
                "text": results["documents"][0][index],
                "metadata": results["metadatas"][0][index],
            }
            for index in range(len(results["ids"][0]))
        ]
        if keyword_weight:
            for record in records:
                semantic_score = 1 / (1 + record["distance"])
                keyword_score = _keyword_overlap_score(query, record["text"])
                record["hybrid_score"] = (
                    1 - keyword_weight
                ) * semantic_score + keyword_weight * keyword_score
            records.sort(key=lambda record: record["hybrid_score"], reverse=True)

        return [
            RetrievalResult(
                rank=index,
                chunk_id=record["chunk_id"],
                distance=record["distance"],
                text=record["text"],
                metadata=record["metadata"],
                hybrid_score=record.get("hybrid_score"),
            )
            for index, record in enumerate(records[:k], start=1)
        ]

    except VectorStoreError:
        raise
    except Exception as e:
        raise VectorStoreError(f"Failed to retrieve results: {e}") from e


def _keyword_overlap_score(query: str, text: str) -> float:
    """Return the fraction of unique query terms present in ``text``."""
    query_terms = set(re.findall(r"\w+", query.casefold()))
    if not query_terms:
        return 0.0
    return len(query_terms & set(re.findall(r"\w+", text.casefold()))) / len(query_terms)
