"""Public document intake API."""

from .basic_chunking import (
    Chunk,
    ChunkingStats,
    TokenChunk,
    TokenChunkingStats,
    calculate_chunk_stats,
    calculate_token_chunk_stats,
    token_chunks,
)
from .chunking import DocumentChunk, chunk_document, chunk_page
from .cleaning import CleanedPage, clean_page, clean_text
from .embeddings import (
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
from .loader import (
    CorpusIngestionResult,
    DocumentLoadError,
    DocumentPage,
    ingest_corpus,
    load_document,
)
from .metadata import tag_chunks

__all__ = [
    "Chunk",
    "ChunkingStats",
    "TokenChunk",
    "TokenChunkingStats",
    "calculate_chunk_stats",
    "calculate_token_chunk_stats",
    "token_chunks",
    "DocumentChunk",
    "chunk_document",
    "chunk_page",
    "DocumentLoadError",
    "DocumentPage",
    "load_document",
    "CleanedPage",
    "clean_page",
    "clean_text",
    "CorpusIngestionResult",
    "ingest_corpus",
    "tag_chunks",
]
