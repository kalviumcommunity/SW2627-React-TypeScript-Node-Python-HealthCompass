"""Load local TXT and text-based PDF documents without altering extracted text."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Mapping

import pymupdf


class DocumentLoadError(ValueError):
    """A source could not be loaded into usable text."""


@dataclass(frozen=True)
class DocumentPage:
    """One source page; PDF page numbers are one-based, TXT has no page number."""

    document_id: str
    source: str
    filename: str
    page_number: int | None
    text: str
    metadata: dict[str, str]


def load_document(
    path: str | Path, *, metadata: Mapping[str, str] | None = None
) -> list[DocumentPage]:
    """Extract a document, preserving caller metadata and original PDF positions.

    Identity is the SHA-256 of source bytes, not a logical guideline/version ID.
    Supplied metadata is descriptive: this loader does not approve documents.
    Empty PDF pages are retained when at least one page contains text.
    """
    source = Path(path).expanduser().resolve()
    if source.suffix.lower() not in {".txt", ".pdf"}:
        raise DocumentLoadError("Unsupported file type; supported formats are TXT and PDF.")
    if metadata is not None and any(
        not isinstance(key, str) or not isinstance(value, str) for key, value in metadata.items()
    ):
        raise DocumentLoadError("Metadata keys and values must be strings.")
    try:
        content = source.read_bytes()
    except OSError as exc:
        raise DocumentLoadError(f"Cannot read source '{source}': {exc.strerror}") from exc
    if not content:
        raise DocumentLoadError("Document is empty.")

    if source.suffix.lower() == ".txt":
        try:
            pages = [(None, content.decode("utf-8-sig"))]
        except UnicodeDecodeError as exc:
            raise DocumentLoadError("TXT documents must use UTF-8 encoding.") from exc
    else:
        try:
            with pymupdf.open(stream=content, filetype="pdf") as document:
                if document.needs_pass:
                    raise DocumentLoadError("Password-protected PDFs are not supported.")
                pages = [(index + 1, page.get_text()) for index, page in enumerate(document)]
        except DocumentLoadError:
            raise
        except (RuntimeError, ValueError) as exc:
            raise DocumentLoadError(
                "Cannot extract PDF; the file may be invalid or damaged."
            ) from exc

    if not any(text.strip() for _, text in pages):
        raise DocumentLoadError("Document contains no extractable text; scanned PDFs require OCR.")
    document_id = sha256(content).hexdigest()
    return [
        DocumentPage(
            document_id=document_id,
            source=str(source),
            filename=source.name,
            page_number=number,
            text=text,
            metadata=dict(metadata or {}),
        )
        for number, text in pages
    ]
