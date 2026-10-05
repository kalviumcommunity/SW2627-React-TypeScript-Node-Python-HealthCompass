"""RAG (Retrieval-Augmented Generation) module for HealthCompass."""

from .citations import Citation, CitationResult, format_citations
from .context_injection import (
    AugmentedPromptResult,
    ContextAssemblyResult,
    assemble_context,
    build_augmented_prompt,
    count_tokens,
    format_chunk_with_source,
    get_max_context_tokens,
)
from .conversational import condense_followup_question
from .generator import generate_grounded_answer, generate_grounded_answer_stream
from .guardrails import (
    STANDARD_REFUSAL,
    GuardrailResult,
    check_faithfulness,
    check_retrieval_guardrails,
    is_refusal,
)
from .pipeline import RAGPipeline, RAGResponse
from .reranker import compute_lexical_score, rerank_chunks

__all__ = [
    "AugmentedPromptResult",
    "Citation",
    "CitationResult",
    "ContextAssemblyResult",
    "GuardrailResult",
    "RAGPipeline",
    "RAGResponse",
    "STANDARD_REFUSAL",
    "assemble_context",
    "build_augmented_prompt",
    "check_faithfulness",
    "check_retrieval_guardrails",
    "compute_lexical_score",
    "condense_followup_question",
    "count_tokens",
    "format_citations",
    "format_chunk_with_source",
    "generate_grounded_answer",
    "generate_grounded_answer_stream",
    "get_max_context_tokens",
    "is_refusal",
    "rerank_chunks",
]
