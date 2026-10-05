"""Store embedded document chunks in the configured vector database."""

from collections.abc import Iterable

import chromadb

from ..vector_store import BatchUpsertResult, VectorRecord, upsert_records
from .embeddings import EmbeddedChunk, generate_chunk_id


def to_vector_record(chunk: EmbeddedChunk) -> VectorRecord:
    """Convert an embedded chunk into a record with a stable content-derived ID."""
    chunk_data = {
        "text": chunk.text,
        "source": chunk.source,
        "filename": chunk.filename,
        "chunk_id": chunk.chunk_id,
        "metadata": chunk.metadata,
    }
    metadata = {
        **chunk.metadata,
        "source": chunk.source,
        "filename": chunk.filename,
        "chunk_id": str(chunk.chunk_id),
    }
    return VectorRecord(
        id=generate_chunk_id(chunk_data),
        embedding=chunk.embedding,
        text=chunk.text,
        metadata=metadata,
    )


def index_embedded_chunks(
    collection: chromadb.Collection,
    embedded_chunks: Iterable[EmbeddedChunk],
    batch_size: int = 100,
) -> BatchUpsertResult:
    """Batch-upsert embedded chunks and return count and failure details."""
    records = [to_vector_record(chunk) for chunk in embedded_chunks]
    return upsert_records(collection, records, batch_size=batch_size)
