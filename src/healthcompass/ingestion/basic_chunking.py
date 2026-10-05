"""Original single-page baselines retained for compatibility and comparison."""

from bisect import bisect_right
from dataclasses import dataclass
from typing import List

import tiktoken

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


@dataclass
class TokenChunk:
    """A text chunk with token count and source metadata for RAG retrieval."""

    text: str
    source: str
    filename: str
    chunk_id: int
    token_count: int
    metadata: dict[str, str]


@dataclass
class TokenChunkingStats:
    """Statistics about token-based chunking results."""

    chunk_count: int
    total_tokens: int
    avg_token_count: float
    min_token_count: int
    max_token_count: int


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


def token_chunks(
    text: str,
    source: str,
    filename: str,
    size: int = 400,
    overlap: int = 60,
    metadata: dict[str, str] | None = None,
    encoding_name: str = "cl100k_base",
) -> List[TokenChunk]:
    """Split text into token-aware chunks with overlap.

    Args:
        text: The text to chunk
        source: Source file path
        filename: Source filename
        size: Target chunk size in tokens
        overlap: Overlap between consecutive chunks in tokens
        metadata: Optional metadata to preserve
        encoding_name: Tiktoken encoding name (default: cl100k_base)

    Returns:
        List of TokenChunk objects with token counts

    Token-based sizing uses the model's actual unit of processing. A single
    Unicode character can span multiple tokens; those tokens stay together so
    decoded chunks never contain replacement characters.
    """
    if type(size) is not int or size < 1:
        raise ValueError("size must be a positive integer")
    if type(overlap) is not int or not 0 <= overlap < size:
        raise ValueError("overlap must satisfy 0 <= overlap < size")
    if metadata is None:
        metadata = {}

    if not text.strip():
        return []

    enc = tiktoken.get_encoding(encoding_name)
    # Treat literal tokenizer control strings as document content. Source
    # documents can legitimately contain values such as ``<|endoftext|>``.
    tokens = enc.encode(text, disallowed_special=())

    if not tokens:
        return []

    boundaries = [0]
    encoded_bytes = bytearray()
    for index, token in enumerate(tokens, start=1):
        encoded_bytes.extend(enc.decode_single_token_bytes(token))
        try:
            encoded_bytes.decode("utf-8")
        except UnicodeDecodeError:
            continue
        boundaries.append(index)

    chunks = []
    start = 0
    chunk_id = 0

    while start < len(tokens):
        desired_end = min(start + size, len(tokens))
        end = boundaries[bisect_right(boundaries, desired_end) - 1]
        if end == start:
            # A Unicode code point may need more than ``size`` tokens. Keep it
            # intact and allow that one chunk to exceed the target.
            end = boundaries[bisect_right(boundaries, start)]
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        token_count = len(chunk_tokens)

        # Only add non-empty chunks
        if chunk_text.strip():
            chunks.append(
                TokenChunk(
                    text=chunk_text,
                    source=source,
                    filename=filename,
                    chunk_id=chunk_id,
                    token_count=token_count,
                    metadata=dict(metadata),
                )
            )
            chunk_id += 1

        # Move start position with overlap
        if end >= len(tokens):
            break
        desired_start = end - overlap
        next_start = boundaries[bisect_right(boundaries, desired_start) - 1]
        # A boundary may fall exactly on the current start when the overlap is
        # larger than the preceding Unicode-safe span. Advancing without
        # overlap is preferable to looping forever.
        start = next_start if next_start > start else end

    return chunks


def calculate_token_chunk_stats(chunks: List[TokenChunk]) -> TokenChunkingStats:
    """Calculate statistics about token-based chunking results.

    Args:
        chunks: List of TokenChunk objects

    Returns:
        TokenChunkingStats with count and token statistics
    """
    if not chunks:
        return TokenChunkingStats(
            chunk_count=0, total_tokens=0, avg_token_count=0.0, min_token_count=0, max_token_count=0
        )

    token_counts = [chunk.token_count for chunk in chunks]

    return TokenChunkingStats(
        chunk_count=len(chunks),
        total_tokens=sum(token_counts),
        avg_token_count=sum(token_counts) / len(token_counts),
        min_token_count=min(token_counts),
        max_token_count=max(token_counts),
    )
