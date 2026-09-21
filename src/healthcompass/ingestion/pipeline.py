"""Run document loading, cleaning, chunking and metadata tagging as one job."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from .basic_chunking import token_chunks
from .cleaning import clean_page
from .loader import DocumentLoadError, load_document
from .metadata import tag_chunks


@dataclass
class IngestionResult:
    """Complete outcome of a corpus ingestion run."""

    files: list[Path]
    docs: int
    chunks: list[dict[str, object]]
    failures: list[tuple[str, str]]

    def __iter__(self):
        """Allow callers to unpack the result as ``files, docs, chunks, failures``."""
        yield self.files
        yield self.docs
        yield self.chunks
        yield self.failures

    @property
    def total_files(self) -> int:
        return len(self.files)


def ingest(
    folder: str | Path,
    *,
    size: int = 400,
    overlap: int = 60,
    boilerplate_lines: Iterable[str] = (),
    metadata: Mapping[str, str] | None = None,
    encoding_name: str = "cl100k_base",
) -> IngestionResult:
    """Process every file under ``folder`` and retain failures for inspection.

    A document counts as ingested only when loading, cleaning and chunking all of
    its pages succeeds. Unsupported and malformed files are included in
    ``files`` and recorded in ``failures`` instead of stopping the run.
    """
    directory = Path(folder).expanduser().resolve()
    if not directory.is_dir():
        raise DocumentLoadError(f"Directory does not exist: {directory}")

    files = sorted(path for path in directory.rglob("*") if path.is_file())
    chunks: list[dict[str, object]] = []
    failures: list[tuple[str, str]] = []
    docs = 0

    for path in files:
        try:
            if path.is_symlink():
                raise DocumentLoadError("Symbolic links are not ingested")

            pages = load_document(path, metadata=metadata)
            file_chunks: list[dict[str, object]] = []
            for page in pages:
                cleaned = clean_page(page, boilerplate_lines=boilerplate_lines)
                tokenized = token_chunks(
                    cleaned.text,
                    source=cleaned.source,
                    filename=cleaned.filename,
                    size=size,
                    overlap=overlap,
                    metadata=cleaned.metadata,
                    encoding_name=encoding_name,
                )
                tagged = tag_chunks(
                    cleaned.filename,
                    [chunk.text for chunk in tokenized],
                    metadata={
                        **cleaned.metadata,
                        "document_id": cleaned.document_id,
                        "page_number": cleaned.page_number,
                    },
                )
                for record, chunk in zip(tagged, tokenized, strict=True):
                    record["metadata"].update(
                        chunk_id=chunk.chunk_id,
                        token_count=chunk.token_count,
                    )
                file_chunks.extend(tagged)

            chunks.extend(file_chunks)
            docs += 1
        except Exception as exc:
            failures.append((path.name, str(exc)))

    return IngestionResult(files=files, docs=docs, chunks=chunks, failures=failures)