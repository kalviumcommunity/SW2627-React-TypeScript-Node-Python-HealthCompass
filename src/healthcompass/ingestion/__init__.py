"""Public document intake API."""

from .loader import DocumentLoadError, DocumentPage, load_document

__all__ = ["DocumentLoadError", "DocumentPage", "load_document"]
