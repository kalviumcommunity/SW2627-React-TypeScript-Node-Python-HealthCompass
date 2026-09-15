"""Deterministic character-based chunking with offsets into the supplied page text."""

import json
import re
from bisect import bisect_right
from collections.abc import Iterable
from dataclasses import dataclass
from hashlib import sha256
from typing import Literal

from .cleaning import CleanedPage
from .loader import DocumentPage

ChunkStrategy = Literal["fixed", "paragraph"]
DEFAULT_MAX_CHARS = 1000
CHUNKING_VERSION = "1"
PARAGRAPH_BREAK = re.compile(r"(?:\r?\n[ \t]*){2,}|\r[ \t]*\r")


@dataclass(frozen=True)
class DocumentChunk:
    """One exact slice; offsets are zero-based Unicode character positions, end exclusive."""

    chunk_id: str
    document_id: str
    source: str
    filename: str
    page_number: int | None
    chunk_index: int
    start_char: int
    end_char: int
    text: str
    metadata: dict[str, str]
    strategy: ChunkStrategy
    max_chars: int
    input_kind: str
    input_sha256: str
    chunking_version: str = CHUNKING_VERSION


def _validate_options(strategy: str, max_chars: int) -> None:
    if strategy not in {"fixed", "paragraph"}:
        raise ValueError("Chunk strategy must be 'fixed' or 'paragraph'")
    if type(max_chars) is not int or max_chars < 1:
        raise ValueError("max_chars must be a positive integer")


def chunk_page(
    page: DocumentPage, *, strategy: ChunkStrategy = "paragraph", max_chars: int = DEFAULT_MAX_CHARS
) -> list[DocumentChunk]:
    """Split one page without overlap or content rewriting.

    Fixed windows cut every max_chars. Paragraph windows prefer the last paragraph
    boundary within that limit; oversized paragraphs fall back to a hard cut.
    Blank-only slices produce no chunks. Chunks never cross source page boundaries.
    """
    _validate_options(strategy, max_chars)
    text = page.text
    boundaries = [match.end() for match in PARAGRAPH_BREAK.finditer(text)]
    input_hash = sha256(text.encode("utf-8")).hexdigest()
    input_kind = "cleaned" if isinstance(page, CleanedPage) else "extracted"
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if strategy == "paragraph" and end < len(text):
            boundary_index = bisect_right(boundaries, end) - 1
            if boundary_index >= 0 and boundaries[boundary_index] > start:
                end = boundaries[boundary_index]
        content = text[start:end]
        if content.strip():
            identity = json.dumps(
                [
                    CHUNKING_VERSION,
                    page.document_id,
                    page.page_number,
                    input_kind,
                    input_hash,
                    strategy,
                    max_chars,
                    start,
                    end,
                ],
                separators=(",", ":"),
            )
            chunks.append(
                DocumentChunk(
                    chunk_id=sha256(identity.encode("utf-8")).hexdigest(),
                    document_id=page.document_id,
                    source=page.source,
                    filename=page.filename,
                    page_number=page.page_number,
                    chunk_index=len(chunks),
                    start_char=start,
                    end_char=end,
                    text=content,
                    metadata=dict(page.metadata),
                    strategy=strategy,
                    max_chars=max_chars,
                    input_kind=input_kind,
                    input_sha256=input_hash,
                )
            )
        start = end
    return chunks


def chunk_document(
    pages: Iterable[DocumentPage],
    *,
    strategy: ChunkStrategy = "paragraph",
    max_chars: int = DEFAULT_MAX_CHARS,
) -> list[DocumentChunk]:
    """Chunk pages in input order; chunk_index restarts on each page."""
    _validate_options(strategy, max_chars)
    return [
        chunk
        for page in pages
        for chunk in chunk_page(page, strategy=strategy, max_chars=max_chars)
    ]
