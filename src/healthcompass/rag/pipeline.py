"""End-to-end RAG pipeline orchestrator for HealthCompass."""

import time
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional

from healthcompass.rag.citations import Citation, format_citations
from healthcompass.rag.context_injection import build_augmented_prompt, get_max_context_tokens
from healthcompass.rag.conversational import condense_followup_question
from healthcompass.rag.generator import generate_grounded_answer, generate_grounded_answer_stream
from healthcompass.rag.guardrails import (
    STANDARD_REFUSAL,
    check_faithfulness,
    check_retrieval_guardrails,
    is_refusal,
)
from healthcompass.rag.reranker import rerank_chunks
from healthcompass.vector_store import RetrievalResult, initialize_vector_store, retrieve


@dataclass
class RAGResponse:
    """Complete structured response from the RAG pipeline."""

    question: str
    condensed_query: str
    answer: str
    citations: List[Citation]
    sources: List[Dict[str, Any]]
    context_tokens: int
    chunks_retrieved: int
    chunks_used: int
    is_refusal: bool
    latency_ms: float
    faithfulness_score: float


class RAGPipeline:
    """Orchestrates end-to-end Retrieval-Augmented Generation for HealthCompass."""

    def __init__(
        self,
        collection=None,
        client=None,
        default_candidate_k: int = 6,
        default_top_k: int = 3,
        default_keyword_weight: float = 0.2,
        max_context_tokens: Optional[int] = None,
    ):
        """Initialize the RAG pipeline.

        Args:
            collection: Optional Chroma collection. If None, initialized on demand.
            client: Optional OpenAI client.
            default_candidate_k: Number of candidates to retrieve initially.
            default_top_k: Number of chunks to select after re-ranking.
            default_keyword_weight: Blend factor for hybrid search (0=dense, 1=sparse).
            max_context_tokens: Maximum tokens permitted in context assembly.
        """
        self._collection = collection
        self.client = client
        self.default_candidate_k = default_candidate_k
        self.default_top_k = default_top_k
        self.default_keyword_weight = default_keyword_weight
        self.max_context_tokens = max_context_tokens or get_max_context_tokens()

    @property
    def collection(self):
        """Get or lazily initialize the Chroma collection."""
        if self._collection is None:
            self._collection = initialize_vector_store()
        return self._collection

    def run(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        keyword_weight: Optional[float] = None,
        candidate_k: Optional[int] = None,
        top_k: Optional[int] = None,
        enable_rerank: bool = True,
    ) -> RAGResponse:
        """Execute the full RAG pipeline for a question.

        Step 1: Condense follow-up questions if conversation history is present.
        Step 2: Retrieve candidate chunks via vector/hybrid search.
        Step 3: Apply re-ranking to boost exact matches and phrases.
        Step 4: Check hallucination guardrails / refusal conditions.
        Step 5: Assemble token-bounded context and build augmented prompt.
        Step 6: Generate grounded answer.
        Step 7: Parse citations and score faithfulness.
        """
        start_time = time.time()
        k_cand = candidate_k or self.default_candidate_k
        k_final = top_k or self.default_top_k
        kw_weight = keyword_weight if keyword_weight is not None else self.default_keyword_weight

        # 1. Condense follow-up query if history is provided
        condensed_query = condense_followup_question(
            query=question,
            history=history,
            client=self.client,
        )

        # 2. Retrieve candidates from vector store
        try:
            candidates: List[RetrievalResult] = retrieve(
                query=condensed_query,
                collection=self.collection,
                k=k_cand,
                metadata_filter=metadata_filter,
                keyword_weight=kw_weight,
            )
        except Exception:
            candidates = []

        # 3. Guardrails check on retrieved context
        guardrail = check_retrieval_guardrails(candidates)
        if guardrail.should_refuse:
            latency_ms = (time.time() - start_time) * 1000
            return RAGResponse(
                question=question,
                condensed_query=condensed_query,
                answer=guardrail.refusal_message or STANDARD_REFUSAL,
                citations=[],
                sources=[],
                context_tokens=0,
                chunks_retrieved=len(candidates),
                chunks_used=0,
                is_refusal=True,
                latency_ms=round(latency_ms, 2),
                faithfulness_score=1.0,
            )

        # 4. Re-rank candidates to top_k
        if enable_rerank and len(candidates) > 1:
            selected_chunks = rerank_chunks(
                query=condensed_query,
                candidates=candidates,
                top_k=k_final,
            )
        else:
            selected_chunks = candidates[:k_final]

        # 5. Build augmented prompt
        prompt_res = build_augmented_prompt(
            question=condensed_query,
            retrieved_chunks=selected_chunks,
            max_context_tokens=self.max_context_tokens,
        )

        # 6. Generate grounded answer
        raw_answer = generate_grounded_answer(
            prompt=prompt_res.prompt,
            client=self.client,
        )

        # 7. Parse citations and compute faithfulness
        citation_res = format_citations(raw_answer, prompt_res.sources_used)
        faithfulness = check_faithfulness(citation_res.text, prompt_res.context)
        latency_ms = (time.time() - start_time) * 1000

        return RAGResponse(
            question=question,
            condensed_query=condensed_query,
            answer=citation_res.text,
            citations=citation_res.citations,
            sources=prompt_res.sources_used,
            context_tokens=prompt_res.context_tokens,
            chunks_retrieved=len(candidates),
            chunks_used=prompt_res.chunks_used,
            is_refusal=is_refusal(citation_res.text),
            latency_ms=round(latency_ms, 2),
            faithfulness_score=round(faithfulness, 3),
        )

    def run_stream(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        keyword_weight: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> Iterator[str]:
        """Stream generated answer tokens for a question."""
        k_final = top_k or self.default_top_k
        kw_weight = keyword_weight if keyword_weight is not None else self.default_keyword_weight

        condensed_query = condense_followup_question(query=question, history=history, client=self.client)

        try:
            candidates = retrieve(
                query=condensed_query,
                collection=self.collection,
                k=self.default_candidate_k,
                metadata_filter=metadata_filter,
                keyword_weight=kw_weight,
            )
        except Exception:
            candidates = []

        guardrail = check_retrieval_guardrails(candidates)
        if guardrail.should_refuse:
            yield guardrail.refusal_message or STANDARD_REFUSAL
            return

        selected_chunks = rerank_chunks(query=condensed_query, candidates=candidates, top_k=k_final)
        prompt_res = build_augmented_prompt(question=condensed_query, retrieved_chunks=selected_chunks)

        for token in generate_grounded_answer_stream(prompt=prompt_res.prompt, client=self.client):
            yield token
