"""RAG context injection and prompt augmentation."""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import tiktoken

from healthcompass.vector_store import RetrievalResult


@dataclass
class ContextAssemblyResult:
    """Result of context assembly with token budget."""

    context: str
    context_tokens: int
    chunks_used: int
    sources_used: List[Dict[str, Any]]
    chunks_excluded: int


@dataclass
class AugmentedPromptResult:
    """Result of building an augmented prompt."""

    prompt: str
    context: str
    context_tokens: int
    chunks_used: int
    sources_used: List[Dict[str, Any]]
    chunks_excluded: int


def format_chunk_with_source(result: RetrievalResult) -> str:
    """Format a retrieved chunk with a clear source marker.

    Args:
        result: RetrievalResult containing chunk data and metadata

    Returns:
        Formatted string with source marker and chunk text
    """
    # Extract source information from metadata
    source = result.metadata.get("source", "unknown")
    chunk_index = result.metadata.get("chunk_id", str(result.rank))

    # Format: [rank] source#chunk_index
    source_marker = f"[{result.rank}] {source}#{chunk_index}"

    return f"{source_marker}\n{result.text}"


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for
        encoding_name: Name of the tiktoken encoding (default: cl100k_base)

    Returns:
        Number of tokens in the text
    """
    if not text:
        return 0

    enc = tiktoken.get_encoding(encoding_name)
    tokens = enc.encode(text)
    return len(tokens)


def assemble_context(
    retrieved_chunks: List[RetrievalResult],
    max_context_tokens: int = 5000,
    encoding_name: str = "cl100k_base",
) -> ContextAssemblyResult:
    """Assemble context from retrieved chunks with token budget.

    Args:
        retrieved_chunks: List of retrieved chunks in ranking order
        max_context_tokens: Maximum tokens allowed for context
        encoding_name: Name of the tiktoken encoding

    Returns:
        ContextAssemblyResult with assembled context and metadata
    """
    if not retrieved_chunks:
        return ContextAssemblyResult(
            context="",
            context_tokens=0,
            chunks_used=0,
            sources_used=[],
            chunks_excluded=0,
        )

    context_parts = []
    sources_used = []
    tokens_used = 0
    chunks_excluded = 0

    for result in retrieved_chunks:
        # Format the chunk with source marker
        formatted_chunk = format_chunk_with_source(result)

        # Count tokens in this formatted chunk
        chunk_tokens = count_tokens(formatted_chunk, encoding_name)

        # Check if this chunk would exceed the budget
        if tokens_used + chunk_tokens > max_context_tokens:
            chunks_excluded += 1
            continue

        # Add chunk to context
        context_parts.append(formatted_chunk)
        tokens_used += chunk_tokens

        # Track source metadata
        source_info = {
            "source": result.metadata.get("source", "unknown"),
            "chunk_id": result.chunk_id,
            "chunk_index": result.metadata.get("chunk_id", str(result.rank)),
            "rank": result.rank,
            "distance": result.distance,
        }
        sources_used.append(source_info)

    # Join all chunks with double newlines
    context = "\n\n".join(context_parts)

    return ContextAssemblyResult(
        context=context,
        context_tokens=tokens_used,
        chunks_used=len(context_parts),
        sources_used=sources_used,
        chunks_excluded=chunks_excluded,
    )


def build_augmented_prompt(
    question: str,
    retrieved_chunks: List[RetrievalResult],
    max_context_tokens: int = 5000,
    encoding_name: str = "cl100k_base",
    system_instruction: Optional[str] = None,
) -> AugmentedPromptResult:
    """Build an augmented prompt with context and question.

    Args:
        question: User question
        retrieved_chunks: List of retrieved chunks
        max_context_tokens: Maximum tokens for context
        encoding_name: Name of the tiktoken encoding
        system_instruction: Optional custom system instruction

    Returns:
        AugmentedPromptResult with complete prompt and metadata
    """
    # Default system instruction
    if system_instruction is None:
        system_instruction = (
            "You are a grounded assistant.\n"
            "Answer the question using only the provided context.\n"
            "Do not use outside knowledge.\n"
            "If the answer cannot be found in the provided context, say: "
            "'I don't have enough information in the provided context.'\n"
            "When possible, cite the source markers such as [1] or [2]."
        )

    # Assemble context with token budget
    assembly_result = assemble_context(
        retrieved_chunks,
        max_context_tokens=max_context_tokens,
        encoding_name=encoding_name,
    )

    # Build the augmented prompt
    prompt = f"{system_instruction}\n\n"
    prompt += "Context:\n"
    prompt += assembly_result.context
    prompt += "\n\n"
    prompt += f"Question:\n{question}"

    return AugmentedPromptResult(
        prompt=prompt,
        context=assembly_result.context,
        context_tokens=assembly_result.context_tokens,
        chunks_used=assembly_result.chunks_used,
        sources_used=assembly_result.sources_used,
        chunks_excluded=assembly_result.chunks_excluded,
    )


def get_max_context_tokens() -> int:
    """Get maximum context tokens from environment or use default.

    Returns:
        Maximum context tokens
    """
    return int(os.getenv("MAX_CONTEXT_TOKENS", "5000"))
