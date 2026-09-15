"""Load local TXT, Markdown, HTML, and text-based PDF documents without altering extracted text."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Mapping

import pymupdf
from bs4 import BeautifulSoup


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


@dataclass
class CorpusIngestionResult:
    """Result of corpus ingestion with success/failure tracking."""
    
    loaded: list[DocumentPage]
    skipped: list[tuple[str, str]]  # (filename, error_message)
    total_files: int


def load_document(
    path: str | Path, *, metadata: Mapping[str, str] | None = None
) -> list[DocumentPage]:
    """Extract a document, preserving caller metadata and original PDF positions.

    Identity is the SHA-256 of source bytes, not a logical guideline/version ID.
    Supplied metadata is descriptive: this loader does not approve documents.
    Empty PDF pages are retained when at least one page contains text.
    Supports TXT, PDF, Markdown (.md), and HTML (.html, .htm) formats.
    """
    source = Path(path).expanduser().resolve()
    supported_formats = {".txt", ".pdf", ".md", ".html", ".htm"}
    if source.suffix.lower() not in supported_formats:
        raise DocumentLoadError(
            f"Unsupported file type: {source.suffix}. "
            f"Supported formats are TXT, PDF, Markdown (.md), and HTML (.html, .htm)."
        )
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

    suffix = source.suffix.lower()
    
    if suffix == ".txt":
        try:
            text = content.decode("utf-8-sig")
            # Normalize line endings for consistency
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            pages = [(None, text)]
        except UnicodeDecodeError as exc:
            raise DocumentLoadError("TXT documents must use UTF-8 encoding.") from exc
    elif suffix == ".md":
        try:
            text = content.decode("utf-8-sig")
            # Normalize line endings for consistency
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            pages = [(None, text)]
        except UnicodeDecodeError as exc:
            raise DocumentLoadError("Markdown documents must use UTF-8 encoding.") from exc
    elif suffix in {".html", ".htm"}:
        try:
            html_text = content.decode("utf-8-sig", errors="ignore")
            soup = BeautifulSoup(html_text, "html.parser")
            # Get text with space separator and strip whitespace
            text = soup.get_text(" ", strip=True)
            pages = [(None, text)]
        except Exception as exc:
            raise DocumentLoadError(f"Cannot extract HTML content: {exc}") from exc
    else:  # PDF
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


def ingest_corpus(
    directory: str | Path, *, metadata: Mapping[str, str] | None = None
) -> CorpusIngestionResult:
    """Recursively scan a directory and load all supported document formats.
    
    Args:
        directory: Path to directory containing documents
        metadata: Optional metadata to apply to all documents
        
    Returns:
        CorpusIngestionResult with loaded documents and skipped files
        
    One bad file will not terminate the entire ingestion process.
    """
    dir_path = Path(directory).expanduser().resolve()
    if not dir_path.is_dir():
        raise DocumentLoadError(f"Directory does not exist: {dir_path}")
    
    loaded = []
    skipped = []
    total_files = 0
    
    for file_path in dir_path.rglob("*"):
        if not file_path.is_file():
            continue
            
        total_files += 1
        try:
            pages = load_document(file_path, metadata=metadata)
            loaded.extend(pages)
        except DocumentLoadError as exc:
            skipped.append((file_path.name, str(exc)))
        except Exception as exc:
            # Catch unexpected errors but continue processing
            skipped.append((file_path.name, f"Unexpected error: {exc}"))
    
    return CorpusIngestionResult(
        loaded=loaded,
        skipped=skipped,
        total_files=total_files
    )
