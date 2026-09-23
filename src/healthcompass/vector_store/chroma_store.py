"""ChromaDB vector store for HealthCompass RAG system."""

import os
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
class RetrievalResult:
    """A result from similarity search retrieval."""

    rank: int
    chunk_id: str
    distance: float
    text: str
    metadata: Dict[str, Any]


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
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # Vector dimensions for common embedding models
    embedding_dimensions = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    vector_dimension = embedding_dimensions.get(
        embedding_model, 1536
    )  # Default to 1536 for text-embedding-3-small

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
        except:
            collection = client.create_collection(
                name=config.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 200,
                    "hnsw:M": 16,
                },
            )
            print(f"Created new collection: {config.collection_name}")

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

        print(f"Vector database initialized at: {config.db_path}")
        print(f"Collection: {config.collection_name}")
        print(f"Embedding dimension: {config.embedding_dimension}")
        print(f"Embedding model: {config.embedding_model}")

        return collection

    except Exception as e:
        raise VectorStoreError(f"Failed to initialize vector store: {e}")


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
        # Validate vector dimension
        collection_data = collection.get(limit=1, include=["embeddings"])
        if len(collection_data["embeddings"]) > 0:
            expected_dimension = len(collection_data["embeddings"][0])
            if len(record.embedding) != expected_dimension:
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
        raise VectorStoreError(f"Failed to insert record: {e}")


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
        raise VectorStoreError(f"Failed to retrieve record: {e}")


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
        raise VectorStoreError(f"Failed to get collection info: {e}")


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
    if embedding_model is None:
        embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise VectorStoreError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please configure your API key in .env file or environment variables."
        )

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.embeddings.create(input=[query], model=embedding_model)
        return response.data[0].embedding
    except openai.RateLimitError as e:
        raise VectorStoreError(f"Rate limit error during query embedding: {e}")
    except openai.APIError as e:
        raise VectorStoreError(f"API error during query embedding: {e}")
    except Exception as e:
        raise VectorStoreError(f"Failed to embed query: {e}")


def retrieve(
    query: str,
    collection: chromadb.Collection,
    k: int = 3,
    embedding_model: str | None = None,
) -> List[RetrievalResult]:
    """Perform top-k similarity search for a query against the vector database.

    Args:
        query: The user query text
        collection: ChromaDB Collection instance
        k: Number of results to retrieve (default: 3)
        embedding_model: Optional embedding model name, uses environment variable if not provided

    Returns:
        List of RetrievalResult objects ranked by similarity

    Raises:
        VectorStoreError: If retrieval fails or k is invalid
    """
    if k <= 0:
        raise VectorStoreError(f"Invalid k value: {k}. k must be greater than 0.")

    if collection.count() == 0:
        raise VectorStoreError("Cannot retrieve from empty collection.")

    try:
        # Embed the query
        query_embedding = embed_query(query, embedding_model)

        # Perform similarity search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        # Process results
        retrieval_results = []
        for i in range(len(results["ids"][0])):
            retrieval_results.append(
                RetrievalResult(
                    rank=i + 1,
                    chunk_id=results["ids"][0][i],
                    distance=results["distances"][0][i],
                    text=results["documents"][0][i],
                    metadata=results["metadatas"][0][i],
                )
            )

        return retrieval_results

    except VectorStoreError:
        raise
    except Exception as e:
        raise VectorStoreError(f"Failed to retrieve results: {e}")
