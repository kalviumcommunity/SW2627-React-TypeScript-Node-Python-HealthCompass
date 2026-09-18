"""Attach source metadata to chunks before indexing or embedding."""

from collections.abc import Iterable, Mapping
from typing import TypeAlias

ChunkInput: TypeAlias = str | tuple[str, int]


def tag_chunks(
    source: str,
    chunks: Iterable[ChunkInput],
    *,
    metadata: Mapping[str, object] | None = None,
) -> list[dict[str, object]]:
    """Return chunks as text-plus-metadata records suitable for indexing.

    Chunk tuples contain ``(text, char_start)``. Bare strings are also accepted
    when offsets are unavailable; every record still has the same metadata keys.
    Caller metadata can add fields such as ``section``, ``page`` or
    ``effective_date`` without replacing the required source fields.
    """
    if not isinstance(source, str) or not source:
        raise ValueError("source must be a nonempty string")
    if metadata is not None and not isinstance(metadata, Mapping):
        raise ValueError("metadata must be a mapping")

    tagged = []
    for index, chunk in enumerate(chunks):
        if isinstance(chunk, str):
            text, char_start = chunk, None
        elif isinstance(chunk, tuple) and len(chunk) == 2:
            text, char_start = chunk
            if not isinstance(char_start, int) or char_start < 0:
                raise ValueError("char_start must be a non-negative integer")
        else:
            raise ValueError("chunks must contain strings or (text, char_start) tuples")
        if not isinstance(text, str):
            raise ValueError("chunk text must be a string")

        chunk_metadata = dict(metadata or {})
        chunk_metadata.update(source=source, chunk_index=index, char_start=char_start)
        tagged.append({"text": text, "metadata": chunk_metadata})
    return tagged