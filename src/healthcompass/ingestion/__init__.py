"""Public document intake API."""

from .chunking import Chunk, ChunkingStats, calculate_chunk_stats, chunk_document
from .cleaning import CleanedPage, clean_page, clean_text
from .loader import (
    CorpusIngestionResult,
    DocumentLoadError,
    DocumentPage,
    ingest_corpus,
    load_document,
)

__all__ = [
    "DocumentLoadError",
    "DocumentPage",
    "load_document",
    "CleanedPage",
    "clean_page",
    "clean_text",
    "CorpusIngestionResult",
    "ingest_corpus",
    "Chunk",
    "ChunkingStats",
    "calculate_chunk_stats",
    "chunk_document",
]
