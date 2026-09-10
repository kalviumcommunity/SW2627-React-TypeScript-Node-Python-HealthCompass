"""Conservative, deterministic cleanup between extraction and chunking."""

from dataclasses import dataclass
import re
import unicodedata
from collections.abc import Iterable

from .loader import DocumentPage

CLEANING_VERSION = "1"
_HORIZONTAL_SPACE = re.compile(r"[^\S\n]+")
_CONTROL_NOISE = re.compile(r"[\x00-\x08\x0b\x0e-\x1f\x7f]")


@dataclass(frozen=True)
class CleanedPage(DocumentPage):
    """Cleaned text plus raw extraction and an audit of configured removals."""

    original_text: str
    cleaning_version: str
    removed_boilerplate_lines: tuple[str, ...]
    warnings: tuple[str, ...]


def _normalize(text: str) -> str:
    # NFC preserves compatibility distinctions such as superscripts and units.
    text = unicodedata.normalize("NFC", text).lstrip("\ufeff")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u2028", "\n").replace("\u2029", "\n\n").replace("\f", "\n\n")
    # Replace noise with a separator so adjacent words/numbers do not concatenate.
    text = _CONTROL_NOISE.sub(" ", text)
    return "\n".join(_HORIZONTAL_SPACE.sub(" ", line).strip() for line in text.split("\n"))


def _clean(text: str, boilerplate_lines: Iterable[str]) -> tuple[str, tuple[str, ...]]:
    if isinstance(boilerplate_lines, str):
        raise ValueError("boilerplate_lines must be a collection of complete lines")
    configured = set()
    for line in boilerplate_lines:
        if not isinstance(line, str):
            raise ValueError("Boilerplate entries must be strings")
        normalized = _normalize(line)
        if not normalized or "\n" in normalized:
            raise ValueError("Each boilerplate entry must be one nonempty line")
        configured.add(normalized)
    lines = _normalize(text).split("\n")
    start, end = 0, len(lines)
    removed_start, removed_end = [], []
    while start < end and (not lines[start] or lines[start] in configured):
        if lines[start]:
            removed_start.append(lines[start])
        start += 1
    while end > start and (not lines[end - 1] or lines[end - 1] in configured):
        if lines[end - 1]:
            removed_end.append(lines[end - 1])
        end -= 1
    # Preserve line/paragraph boundaries and list items, limit surplus blank lines.
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(lines[start:end])).strip()
    return cleaned, tuple(removed_start + list(reversed(removed_end)))


def clean_text(text: str, *, boilerplate_lines: Iterable[str] = ()) -> str:
    """Normalize text and remove exact configured lines only at page boundaries.

    No lowercasing, dehyphenation, line reflow, guessed OCR repair, or automatic
    repeated-line removal. Call once per source page, not on concatenated PDFs.
    """
    return _clean(text, boilerplate_lines)[0]


def clean_page(page: DocumentPage, *, boilerplate_lines: Iterable[str] = ()) -> CleanedPage:
    """Return a new record without changing extraction, source identity or metadata.

    Re-cleaning a CleanedPage starts from its original extraction, so a new policy
    never loses the original evidence. Empty results retain their page position.
    """
    original = page.original_text if isinstance(page, CleanedPage) else page.text
    text, removed = _clean(original, boilerplate_lines)
    warnings = ("empty_after_cleaning",) if not text else ()
    return CleanedPage(
        document_id=page.document_id, source=page.source, filename=page.filename,
        page_number=page.page_number, text=text, metadata=dict(page.metadata),
        original_text=original, cleaning_version=CLEANING_VERSION,
        removed_boilerplate_lines=removed, warnings=warnings,
    )
