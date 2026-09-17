"""Embedding generation for RAG using OpenAI-compatible APIs."""

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

import openai
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


@dataclass
class EmbeddedChunk:
    """A text chunk with its embedding vector and metadata for RAG retrieval."""

    text: str
    source: str
    filename: str
    chunk_id: int
    metadata: dict[str, str]
    embedding: List[float]
    embedding_model: str


@dataclass
class EmbeddingManifest:
    """Manifest information for a set of embedded chunks."""

    embedding_model: str
    chunk_count: int
    vector_dimension: int
    created_at: str
    source_files: List[str]


@dataclass
class EmbeddingResult:
    """Result of embedding generation with validation information."""

    embedded_chunks: List[EmbeddedChunk]
    manifest: EmbeddingManifest
    validation_passed: bool
    validation_errors: List[str] = field(default_factory=list)


class EmbeddingError(Exception):
    """Custom exception for embedding-related errors."""

    pass


def get_embedding_config() -> tuple[str, str, str]:
    """Get embedding configuration from environment variables.

    Returns:
        Tuple of (api_key, model, base_url)

    Raises:
        EmbeddingError: If API key is not configured
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        raise EmbeddingError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please configure your API key in .env file or environment variables."
        )

    return api_key, model, base_url


def generate_embeddings(
    chunks: List[dict],
    embedding_model: str | None = None,
    batch_size: int = 100,
) -> EmbeddingResult:
    """Generate embeddings for a list of text chunks using OpenAI-compatible API.

    Args:
        chunks: List of chunk dictionaries with 'text', 'source', 'filename',
                'chunk_id', and 'metadata' keys
        embedding_model: Optional override for embedding model name
        batch_size: Number of chunks to process per API call

    Returns:
        EmbeddingResult with embedded chunks and manifest

    Raises:
        EmbeddingError: If API call fails or validation fails
    """
    if not chunks:
        return EmbeddingResult(
            embedded_chunks=[],
            manifest=EmbeddingManifest(
                embedding_model=embedding_model or "text-embedding-3-small",
                chunk_count=0,
                vector_dimension=0,
                created_at=datetime.now(timezone.utc).isoformat(),
                source_files=[],
            ),
            validation_passed=True,
        )

    try:
        api_key, default_model, base_url = get_embedding_config()
        model = embedding_model or default_model

        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        embedded_chunks = []
        source_files = set()

        # Process chunks in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [chunk["text"] for chunk in batch]

            try:
                response = client.embeddings.create(input=texts, model=model)
            except openai.APIError as e:
                raise EmbeddingError(f"OpenAI API error during embedding generation: {e}")
            except Exception as e:
                raise EmbeddingError(f"Unexpected error during embedding generation: {e}")

            # Validate response length
            if len(response.data) != len(batch):
                raise EmbeddingError(
                    f"API returned {len(response.data)} embeddings for {len(batch)} chunks"
                )

            # Match embeddings to chunks
            for chunk, embedding_data in zip(batch, response.data):
                source_files.add(chunk.get("source", "unknown"))
                embedded_chunks.append(
                    EmbeddedChunk(
                        text=chunk["text"],
                        source=chunk["source"],
                        filename=chunk["filename"],
                        chunk_id=chunk["chunk_id"],
                        metadata=dict(chunk["metadata"]),
                        embedding=embedding_data.embedding,
                        embedding_model=model,
                    )
                )

        # Create manifest
        vector_dimension = len(embedded_chunks[0].embedding) if embedded_chunks else 0
        manifest = EmbeddingManifest(
            embedding_model=model,
            chunk_count=len(embedded_chunks),
            vector_dimension=vector_dimension,
            created_at=datetime.now(timezone.utc).isoformat(),
            source_files=list(source_files),
        )

        # Validate results
        validation_errors = validate_embeddings(embedded_chunks, manifest)

        return EmbeddingResult(
            embedded_chunks=embedded_chunks,
            manifest=manifest,
            validation_passed=len(validation_errors) == 0,
            validation_errors=validation_errors,
        )

    except EmbeddingError:
        raise
    except Exception as e:
        raise EmbeddingError(f"Failed to generate embeddings: {e}")


def validate_embeddings(
    embedded_chunks: List[EmbeddedChunk], manifest: EmbeddingManifest
) -> List[str]:
    """Validate embedded chunks for consistency and correctness.

    Args:
        embedded_chunks: List of embedded chunks to validate
        manifest: Manifest with expected metadata

    Returns:
        List of validation error messages (empty if validation passes)
    """
    errors = []

    if not embedded_chunks:
        if manifest.chunk_count != 0:
            errors.append("Manifest reports non-zero chunk count but no chunks provided")
        return errors

    # Check that all chunks have embeddings
    for i, chunk in enumerate(embedded_chunks):
        if not chunk.embedding:
            errors.append(f"Chunk {i} has empty embedding")

    # Check that all embeddings are lists of numbers
    for i, chunk in enumerate(embedded_chunks):
        if not isinstance(chunk.embedding, list):
            errors.append(f"Chunk {i} embedding is not a list")
        elif not all(isinstance(x, (int, float)) for x in chunk.embedding):
            errors.append(f"Chunk {i} embedding contains non-numeric values")

    # Check that all vectors have the same dimension
    if embedded_chunks:
        dimensions = [len(chunk.embedding) for chunk in embedded_chunks]
        if len(set(dimensions)) > 1:
            errors.append(f"Embeddings have inconsistent dimensions: {set(dimensions)}")

    # Check that number of vectors matches number of chunks
    if len(embedded_chunks) != manifest.chunk_count:
        errors.append(
            f"Chunk count mismatch: {len(embedded_chunks)} chunks vs {manifest.chunk_count} in manifest"
        )

    # Check that each vector is attached to source text and metadata
    for i, chunk in enumerate(embedded_chunks):
        if not chunk.text:
            errors.append(f"Chunk {i} has empty source text")
        if not chunk.source:
            errors.append(f"Chunk {i} has empty source")
        if chunk.chunk_id is None:
            errors.append(f"Chunk {i} has None chunk_id")

    return errors


def prepare_chunks_from_token_chunks(
    token_chunks: List,
) -> List[dict]:
    """Convert TokenChunk objects to dictionaries for embedding generation.

    Args:
        token_chunks: List of TokenChunk objects from chunking module

    Returns:
        List of chunk dictionaries in the format expected by generate_embeddings
    """
    return [
        {
            "text": chunk.text,
            "source": chunk.source,
            "filename": chunk.filename,
            "chunk_id": chunk.chunk_id,
            "metadata": chunk.metadata,
        }
        for chunk in token_chunks
    ]


def prepare_chunks_from_basic_chunks(
    basic_chunks: List,
) -> List[dict]:
    """Convert basic Chunk objects to dictionaries for embedding generation.

    Args:
        basic_chunks: List of Chunk objects from chunking module

    Returns:
        List of chunk dictionaries in the format expected by generate_embeddings
    """
    return [
        {
            "text": chunk.text,
            "source": chunk.source,
            "filename": chunk.filename,
            "chunk_id": chunk.chunk_id,
            "metadata": chunk.metadata,
        }
        for chunk in basic_chunks
    ]
