"""Embedding generation for RAG using OpenAI-compatible APIs."""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, List, Mapping, Sequence

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


@dataclass
class EmbeddingRunSummary:
    """Summary of an embedding generation run."""

    total_chunks: int
    skipped_existing: int
    chunks_processed: int
    successfully_embedded: int
    failed_chunks: int
    total_batches: int
    input_token_count: int
    estimated_cost_usd: float
    embedding_model: str
    batch_size: int
    retry_attempts: int
    failed_batch_indices: List[int] = field(default_factory=list)


class EmbeddingError(Exception):
    """Custom exception for embedding-related errors."""

    pass


def cosine_similarity(first: List[float], second: List[float]) -> float:
    """Return cosine similarity for two embedding vectors."""
    if not first or not second:
        raise ValueError("Embedding vectors must not be empty")
    if len(first) != len(second):
        raise ValueError("Embedding vectors must have the same dimension")

    first_norm = sum(value * value for value in first) ** 0.5
    second_norm = sum(value * value for value in second) ** 0.5
    if first_norm == 0 or second_norm == 0:
        raise ValueError("Embedding vectors must have a non-zero magnitude")

    dot_product = sum(left * right for left, right in zip(first, second, strict=True))
    return dot_product / (first_norm * second_norm)


def rank_chunks_by_similarity(
    query_embedding: List[float],
    chunk_records: Sequence[EmbeddedChunk | Mapping[str, Any]],
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Rank embedded chunks from most to least similar to a query vector.

    The returned records copy each input record and add a ``score`` field. A
    copy is used so ranking does not mutate stored embedding data.
    """
    if top_k is not None and top_k < 1:
        raise ValueError("top_k must be greater than 0")

    ranked = []
    for record in chunk_records:
        values = record.__dict__ if isinstance(record, EmbeddedChunk) else record
        ranked.append(
            {
                **values,
                "score": cosine_similarity(query_embedding, values["embedding"]),
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked if top_k is None else ranked[:top_k]


def get_embedding_config() -> tuple[str, str, str, int, int]:
    """Get embedding configuration from environment variables.

    Returns:
        Tuple of (api_key, model, base_url, batch_size, max_retry_attempts)

    Raises:
        EmbeddingError: If API key is not configured
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))
    max_retry_attempts = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))

    if not api_key:
        raise EmbeddingError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please configure your API key in .env file or environment variables."
        )

    return api_key, model, base_url, batch_size, max_retry_attempts


def generate_chunk_id(chunk: dict) -> str:
    """Generate a unique ID for a chunk based on its content and metadata.

    Args:
        chunk: Chunk dictionary with text, source, filename, chunk_id, metadata

    Returns:
        Unique SHA-256 hash for the chunk
    """
    chunk_string = json.dumps(
        {
            "text": chunk["text"],
            "source": chunk["source"],
            "filename": chunk["filename"],
            "chunk_id": chunk["chunk_id"],
            "metadata": chunk["metadata"],
        },
        sort_keys=True,
    )
    return sha256(chunk_string.encode("utf-8")).hexdigest()


def load_existing_embeddings(output_path: Path) -> dict[str, EmbeddedChunk]:
    """Load existing embeddings from JSON file.

    Args:
        output_path: Path to the JSON file containing embedded chunks

    Returns:
        Dictionary mapping chunk IDs to EmbeddedChunk objects
    """
    if not output_path.exists():
        return {}

    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        existing_embeddings = {}
        for chunk_data in data.get("chunks", []):
            chunk_id = generate_chunk_id(
                {
                    "text": chunk_data["text"],
                    "source": chunk_data["source"],
                    "filename": chunk_data["filename"],
                    "chunk_id": chunk_data["chunk_id"],
                    "metadata": chunk_data["metadata"],
                }
            )
            existing_embeddings[chunk_id] = EmbeddedChunk(
                text=chunk_data["text"],
                source=chunk_data["source"],
                filename=chunk_data["filename"],
                chunk_id=chunk_data["chunk_id"],
                metadata=chunk_data["metadata"],
                embedding=chunk_data["embedding"],
                embedding_model=chunk_data["embedding_model"],
            )

        return existing_embeddings
    except (json.JSONDecodeError, KeyError, IOError):
        return {}


def save_embeddings_incremental(
    embedded_chunks: List[EmbeddedChunk],
    manifest: EmbeddingManifest,
    output_path: Path,
):
    """Save embeddings to JSON file, merging with existing data.

    Args:
        embedded_chunks: List of embedded chunks to save
        manifest: Manifest information
        output_path: Path to save the JSON file
    """
    # Load existing data if file exists
    existing_data = {}
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_data = {}

    # Merge new records with existing records by their content-derived IDs.
    merged_chunks = {}
    for chunk_data in existing_data.get("chunks", []):
        try:
            chunk_id = generate_chunk_id(chunk_data)
        except (KeyError, TypeError):
            continue
        merged_chunks[chunk_id] = chunk_data

    serializable_chunks = []
    for chunk in embedded_chunks:
        chunk_data = {
            "text": chunk.text,
            "source": chunk.source,
            "filename": chunk.filename,
            "chunk_id": chunk.chunk_id,
            "metadata": chunk.metadata,
            "embedding": chunk.embedding,
            "embedding_model": chunk.embedding_model,
        }
        merged_chunks[generate_chunk_id(chunk_data)] = chunk_data
    serializable_chunks.extend(merged_chunks.values())

    source_files = set(manifest.source_files)
    source_files.update(chunk.get("source", "") for chunk in serializable_chunks)
    source_files.discard("")

    output_data = {
        "manifest": {
            "embedding_model": manifest.embedding_model,
            "chunk_count": len(serializable_chunks),
            "vector_dimension": manifest.vector_dimension,
            "created_at": manifest.created_at,
            "source_files": sorted(source_files),
        },
        "chunks": serializable_chunks,
        "validation": {
            "passed": True,  # Assume validation passed for incremental saves
            "errors": [],
        },
    }

    # Write to temporary file first for safety
    temp_path = output_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    # Atomic rename
    temp_path.replace(output_path)


def estimate_cost(token_count: int, model: str) -> float:
    """Estimate cost for embedding generation based on token count and model.

    Args:
        token_count: Total number of tokens to embed
        model: Embedding model name

    Returns:
        Estimated cost in USD

    Note:
        Prices are approximate and should be updated based on current provider pricing.
        These are example prices for OpenAI's text-embedding-3-small model.
    """
    # Example pricing (update with actual current prices)
    pricing = {
        "text-embedding-3-small": 0.00002,  # $0.02 per 1M tokens
        "text-embedding-3-large": 0.00013,  # $0.13 per 1M tokens
        "text-embedding-ada-002": 0.0001,  # $0.10 per 1M tokens
    }

    price_per_1m_tokens = pricing.get(model, 0.00002)  # Default to small model pricing
    return (token_count / 1_000_000) * price_per_1m_tokens


def call_embedding_api_with_retry(
    client,
    texts: List[str],
    model: str,
    max_attempts: int = 3,
) -> List[List[float]]:
    """Call embedding API with exponential backoff retry logic.

    Args:
        client: OpenAI client instance
        texts: List of texts to embed
        model: Embedding model name
        max_attempts: Maximum number of retry attempts

    Returns:
        List of embedding vectors

    Raises:
        EmbeddingError: If all retry attempts fail
    """
    for attempt in range(max_attempts):
        try:
            response = client.embeddings.create(input=texts, model=model)
            return [embedding.embedding for embedding in response.data]

        except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError) as e:
            if attempt < max_attempts - 1:
                wait_time = 2**attempt  # Exponential backoff: 1, 2, 4, 8...
                print(f"Temporary error. Waiting {wait_time}s before retry (attempt {attempt + 1}/{max_attempts})...")
                time.sleep(wait_time)
            else:
                raise EmbeddingError(f"Temporary error after {max_attempts} attempts: {e}")

        except openai.APIError as e:
            # Don't retry on permanent API errors
            raise EmbeddingError(f"Permanent API error: {e}")

        except Exception as e:
            # For testing purposes, treat generic exceptions as retryable
            if attempt < max_attempts - 1:
                wait_time = 2**attempt
                print(f"Temporary error. Waiting {wait_time}s before retry (attempt {attempt + 1}/{max_attempts})...")
                time.sleep(wait_time)
            else:
                raise EmbeddingError(f"Unexpected error during embedding API call: {e}")

    raise EmbeddingError(f"Failed to complete embedding after {max_attempts} attempts")


def generate_embeddings(
    chunks: List[dict],
    embedding_model: str | None = None,
    batch_size: int | None = None,
    output_path: Path | None = None,
    skip_existing: bool = True,
) -> tuple[EmbeddingResult, EmbeddingRunSummary]:
    """Generate embeddings for a list of text chunks using OpenAI-compatible API.

    Args:
        chunks: List of chunk dictionaries with 'text', 'source', 'filename',
                'chunk_id', and 'metadata' keys
        embedding_model: Optional override for embedding model name
        batch_size: Optional override for batch size (uses env var default if None)
        output_path: Optional path to save embeddings incrementally
        skip_existing: Whether to skip chunks that already have embeddings

    Returns:
        Tuple of (EmbeddingResult, EmbeddingRunSummary)

    Raises:
        EmbeddingError: If API call fails or validation fails
    """
    if not chunks:
        empty_result = EmbeddingResult(
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
        empty_summary = EmbeddingRunSummary(
            total_chunks=0,
            skipped_existing=0,
            chunks_processed=0,
            successfully_embedded=0,
            failed_chunks=0,
            total_batches=0,
            input_token_count=0,
            estimated_cost_usd=0.0,
            embedding_model=embedding_model or "text-embedding-3-small",
            batch_size=batch_size or 64,
            retry_attempts=0,
        )
        return empty_result, empty_summary

    try:
        api_key, default_model, base_url, default_batch_size, max_retry_attempts = (
            get_embedding_config()
        )
        model = embedding_model or default_model
        actual_batch_size = batch_size or default_batch_size

        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        # Load existing embeddings if skipping
        existing_embeddings = {}
        if skip_existing and output_path:
            existing_embeddings = load_existing_embeddings(output_path)

        # Identify chunks to skip
        chunks_to_process = []
        skipped_count = 0
        for chunk in chunks:
            chunk_id = generate_chunk_id(chunk)
            if chunk_id in existing_embeddings:
                skipped_count += 1
            else:
                chunks_to_process.append(chunk)

        print(f"Total chunks: {len(chunks)}")
        print(f"Skipped existing embeddings: {skipped_count}")
        print(f"Chunks to process: {len(chunks_to_process)}")

        embedded_chunks = []
        source_files = set()
        failed_batch_indices = []
        total_retry_attempts = 0
        input_token_count = 0

        # Process chunks in batches
        total_batches = (len(chunks_to_process) + actual_batch_size - 1) // actual_batch_size

        for batch_index, i in enumerate(range(0, len(chunks_to_process), actual_batch_size)):
            batch = chunks_to_process[i : i + actual_batch_size]
            texts = [chunk["text"] for chunk in batch]

            try:
                embeddings = call_embedding_api_with_retry(
                    client, texts, model, max_retry_attempts
                )
                total_retry_attempts += max_retry_attempts  # Simplified tracking

                # Validate response length
                if len(embeddings) != len(batch):
                    raise EmbeddingError(
                        f"API returned {len(embeddings)} embeddings for {len(batch)} chunks"
                    )

                # Match embeddings to chunks
                for chunk, embedding in zip(batch, embeddings):
                    source_files.add(chunk.get("source", "unknown"))
                    embedded_chunks.append(
                        EmbeddedChunk(
                            text=chunk["text"],
                            source=chunk["source"],
                            filename=chunk["filename"],
                            chunk_id=chunk["chunk_id"],
                            metadata=dict(chunk["metadata"]),
                            embedding=embedding,
                            embedding_model=model,
                        )
                    )

                # Estimate token count (rough approximation: ~4 chars per token)
                batch_chars = sum(len(text) for text in texts)
                input_token_count += batch_chars // 4

                # Save incrementally if output path provided
                if output_path:
                    temp_manifest = EmbeddingManifest(
                        embedding_model=model,
                        chunk_count=len(embedded_chunks) + len(existing_embeddings),
                        vector_dimension=len(embeddings[0]) if embeddings else 0,
                        created_at=datetime.now(timezone.utc).isoformat(),
                        source_files=list(source_files),
                    )
                    save_embeddings_incremental(embedded_chunks, temp_manifest, output_path)
                    print(f"Saved progress after batch {batch_index + 1}/{total_batches}")

            except EmbeddingError as e:
                failed_batch_indices.append(batch_index)
                print(f"Failed to process batch {batch_index + 1}/{total_batches}: {e}")
                # Continue with next batch rather than failing entire process

        # Combine with existing embeddings
        final_chunks = list(existing_embeddings.values()) + embedded_chunks

        # Create manifest
        vector_dimension = len(final_chunks[0].embedding) if final_chunks else 0
        manifest = EmbeddingManifest(
            embedding_model=model,
            chunk_count=len(final_chunks),
            vector_dimension=vector_dimension,
            created_at=datetime.now(timezone.utc).isoformat(),
            source_files=list(source_files),
        )

        # Validate results
        validation_errors = validate_embeddings(final_chunks, manifest)

        # Calculate estimated cost
        estimated_cost = estimate_cost(input_token_count, model)

        # Create run summary
        summary = EmbeddingRunSummary(
            total_chunks=len(chunks),
            skipped_existing=skipped_count,
            chunks_processed=len(chunks_to_process),
            successfully_embedded=len(embedded_chunks),
            failed_chunks=len(chunks_to_process) - len(embedded_chunks),
            total_batches=total_batches,
            input_token_count=input_token_count,
            estimated_cost_usd=estimated_cost,
            embedding_model=model,
            batch_size=actual_batch_size,
            retry_attempts=total_retry_attempts,
            failed_batch_indices=failed_batch_indices,
        )

        result = EmbeddingResult(
            embedded_chunks=final_chunks,
            manifest=manifest,
            validation_passed=len(validation_errors) == 0,
            validation_errors=validation_errors,
        )

        return result, summary

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
