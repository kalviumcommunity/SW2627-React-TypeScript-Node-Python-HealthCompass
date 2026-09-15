"""Original single-page baselines retained for compatibility and comparison."""

from dataclasses import dataclass
from typing import List

from .loader import DocumentPage


@dataclass(frozen=True)
class Chunk:
    """A text chunk with source metadata for RAG retrieval."""

    text: str
    source: str
    filename: str
    chunk_id: int
    metadata: dict[str, str]


@dataclass
class ChunkingStats:
    """Statistics about chunking results."""

    chunk_count: int
    avg_chunk_size: float
    min_chunk_size: int
    max_chunk_size: int


def fixed_size_chunks(
    text: str,
    source: str,
    filename: str,
    chunk_size: int = 500,
    overlap: int = 100,
    metadata: dict[str, str] | None = None,
) -> List[Chunk]:
    """Split text into fixed-size chunks with overlap.

    Args:
        text: The text to chunk
        source: Source file path
        filename: Source filename
        chunk_size: Target chunk size in characters
        overlap: Overlap between consecutive chunks in characters
        metadata: Optional metadata to preserve

    Returns:
        List of Chunk objects

    Overlap helps preserve context across chunk boundaries for better retrieval.
    """
    if type(chunk_size) is not int or chunk_size < 1:
        raise ValueError("chunk_size must be a positive integer")
    if type(overlap) is not int or not 0 <= overlap < chunk_size:
        raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")
    if metadata is None:
        metadata = {}

    if not text.strip():
        return []

    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]

        # Only add non-empty chunks
        if chunk_text.strip():
            chunks.append(
                Chunk(
                    text=chunk_text,
                    source=source,
                    filename=filename,
                    chunk_id=chunk_id,
                    metadata=dict(metadata),
                )
            )
            chunk_id += 1

        # Move start position with overlap
        if end >= len(text):
            break
        start = end - overlap

    return chunks


def paragraph_chunks(
    text: str, source: str, filename: str, metadata: dict[str, str] | None = None
) -> List[Chunk]:
    """Split text into paragraph-based chunks.

    Args:
        text: The text to chunk
        source: Source file path
        filename: Source filename
        metadata: Optional metadata to preserve

    Returns:
        List of Chunk objects

    Preserves natural paragraph boundaries for better semantic coherence.
    """
    if metadata is None:
        metadata = {}

    if not text.strip():
        return []

    # Split by paragraph boundaries (one or more newlines)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    chunk_id = 0

    for paragraph in paragraphs:
        if paragraph:  # Only add non-empty paragraphs
            chunks.append(
                Chunk(
                    text=paragraph,
                    source=source,
                    filename=filename,
                    chunk_id=chunk_id,
                    metadata=dict(metadata),
                )
            )
            chunk_id += 1

    return chunks


def chunk_document(
    document: DocumentPage, strategy: str = "fixed", chunk_size: int = 500, overlap: int = 100
) -> List[Chunk]:
    """Chunk a document using the specified strategy.

    Args:
        document: DocumentPage with text to chunk
        strategy: Either "fixed" or "paragraph"
        chunk_size: Chunk size for fixed-size strategy
        overlap: Overlap for fixed-size strategy

    Returns:
        List of Chunk objects
    """
    if strategy == "fixed":
        return fixed_size_chunks(
            document.text,
            document.source,
            document.filename,
            chunk_size=chunk_size,
            overlap=overlap,
            metadata=document.metadata,
        )
    elif strategy == "paragraph":
        return paragraph_chunks(
            document.text, document.source, document.filename, metadata=document.metadata
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy}. Use 'fixed' or 'paragraph'.")


def calculate_chunk_stats(chunks: List[Chunk]) -> ChunkingStats:
    """Calculate statistics about chunking results.

    Args:
        chunks: List of Chunk objects

    Returns:
        ChunkingStats with count and size statistics
    """
    if not chunks:
        return ChunkingStats(chunk_count=0, avg_chunk_size=0.0, min_chunk_size=0, max_chunk_size=0)

    sizes = [len(chunk.text) for chunk in chunks]

    return ChunkingStats(
        chunk_count=len(chunks),
        avg_chunk_size=sum(sizes) / len(sizes),
        min_chunk_size=min(sizes),
        max_chunk_size=max(sizes),
    )
