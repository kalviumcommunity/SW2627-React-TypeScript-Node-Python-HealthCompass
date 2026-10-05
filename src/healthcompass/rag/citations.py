"""Source citation and attribution parsing for HealthCompass RAG system."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Citation:
    """Individual citation reference."""

    index: int
    chunk_id: str
    source: str
    section: Optional[str]
    snippet: str
    distance: float


@dataclass
class CitationResult:
    """Structured result containing formatted answer and validated citations."""

    text: str
    citations: List[Citation]
    cited_indices: List[int]
    unmatched_indices: List[int]


def extract_citation_indices(text: str) -> List[int]:
    """Find all numeric citation bracket indices in text, e.g. [1], [2], [1, 2].

    Args:
        text: Text to search.

    Returns:
        List of unique integer citation indices.
    """
    indices = set()
    # Match patterns like [1], [2], [1, 2], [1,2,3]
    matches = re.findall(r"\[([0-9,\s]+)\]", text)
    for match in matches:
        parts = match.split(",")
        for part in parts:
            part = part.strip()
            if part.isdigit():
                indices.add(int(part))
    return sorted(indices)


def format_citations(
    answer: str,
    sources_used: List[Dict[str, Any]],
    auto_append_if_missing: bool = True,
) -> CitationResult:
    """Validate citations in answer against retrieved sources, and build structured citation data.

    Args:
        answer: Generated answer text.
        sources_used: List of source dicts from context assembly (with rank, source, chunk_id, etc.).
        auto_append_if_missing: If True and answer has no citations, append citation markers.

    Returns:
        CitationResult with validated citations and formatted answer.
    """
    extracted_indices = extract_citation_indices(answer)
    source_by_rank: Dict[int, Dict[str, Any]] = {
        int(s.get("rank", idx + 1)): s for idx, s in enumerate(sources_used)
    }

    valid_citations: List[Citation] = []
    unmatched_indices: List[int] = []

    for idx in extracted_indices:
        if idx in source_by_rank:
            src = source_by_rank[idx]
            valid_citations.append(
                Citation(
                    index=idx,
                    chunk_id=src.get("chunk_id", ""),
                    source=src.get("source", "unknown"),
                    section=src.get("section") or src.get("chunk_index"),
                    snippet=src.get("snippet", src.get("text", ""))[:150],
                    distance=float(src.get("distance", 0.0)),
                )
            )
        else:
            unmatched_indices.append(idx)

    final_text = answer

    # If no citation markers were placed by model and we have valid sources,
    # append citations for the primary source(s)
    if not extracted_indices and sources_used and auto_append_if_missing:
        # Avoid appending citations if answer is an explicit refusal
        from healthcompass.rag.guardrails import is_refusal

        if not is_refusal(answer):
            primary_src = sources_used[0]
            final_text = f"{answer} [1]"
            valid_citations.append(
                Citation(
                    index=1,
                    chunk_id=primary_src.get("chunk_id", ""),
                    source=primary_src.get("source", "unknown"),
                    section=primary_src.get("section") or primary_src.get("chunk_index"),
                    snippet=primary_src.get("snippet", primary_src.get("text", ""))[:150],
                    distance=float(primary_src.get("distance", 0.0)),
                )
            )
            extracted_indices = [1]

    return CitationResult(
        text=final_text,
        citations=valid_citations,
        cited_indices=extracted_indices,
        unmatched_indices=unmatched_indices,
    )
