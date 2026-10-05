"""Hallucination guardrails and refusal handling for HealthCompass RAG system."""

import re
from dataclasses import dataclass
from typing import List, Optional

from healthcompass.vector_store import RetrievalResult

STANDARD_REFUSAL = (
    "I do not have enough verified information in the official guidance to answer this question. "
    "Please consult your health supervisor or official circulars for verified instructions."
)

REFUSAL_PHRASES = [
    "i don't have enough information",
    "i do not have enough information",
    "not in the provided context",
    "not mentioned in the context",
    "cannot be found in the provided context",
    "not provided in the context",
    "insufficient information",
    "official guidance does not specify",
]


@dataclass
class GuardrailResult:
    """Result of evaluating retrieval guardrails."""

    should_refuse: bool
    refusal_message: Optional[str] = None
    reason: Optional[str] = None


def is_refusal(text: str) -> bool:
    """Check if generated text is a refusal.

    Args:
        text: Response text to check.

    Returns:
        True if text expresses a refusal based on missing context.
    """
    cleaned = text.lower()
    return any(phrase in cleaned for phrase in REFUSAL_PHRASES)


def check_retrieval_guardrails(
    chunks: List[RetrievalResult],
    max_distance_threshold: float = 1.2,
    min_chunks: int = 1,
) -> GuardrailResult:
    """Evaluate whether retrieved context is sufficient and relevant enough to proceed with generation.

    Args:
        chunks: List of retrieved chunks.
        max_distance_threshold: Maximum allowed vector distance for the top result.
        min_chunks: Minimum number of retrieved chunks required.

    Returns:
        GuardrailResult indicating whether generation should be aborted in favor of a refusal.
    """
    if not chunks or len(chunks) < min_chunks:
        return GuardrailResult(
            should_refuse=True,
            refusal_message=STANDARD_REFUSAL,
            reason="No relevant documents found in knowledge base",
        )

    # If the closest chunk is too distant, refuse to prevent hallucination
    top_distance = chunks[0].distance
    if top_distance > max_distance_threshold:
        return GuardrailResult(
            should_refuse=True,
            refusal_message=STANDARD_REFUSAL,
            reason=f"Top chunk distance ({top_distance:.3f}) exceeds safety threshold ({max_distance_threshold})",
        )

    return GuardrailResult(should_refuse=False)


def check_faithfulness(answer: str, context: str) -> float:
    """Measure the lexical overlap ratio of answer key terms against context.

    Args:
        answer: Generated answer string.
        context: Retrieved context text.

    Returns:
        Faithfulness ratio between 0.0 and 1.0.
    """
    # Extract substantive words (length >= 4) from answer
    answer_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", answer.lower()))
    if not answer_words:
        return 1.0

    context_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", context.lower()))
    supported_words = answer_words & context_words

    return len(supported_words) / len(answer_words)
