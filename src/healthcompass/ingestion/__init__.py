"""Public document intake API."""

from .chunking import DocumentChunk, chunk_document, chunk_page
from .cleaning import CleanedPage, clean_page, clean_text
from .loader import (
    CorpusIngestionResult,
    DocumentLoadError,
    DocumentPage,
    ingest_corpus,
    load_document,
)

__all__ = [
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
]
