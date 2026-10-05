"""Unit tests for the end-to-end RAG pipeline, guardrails, citations, and conversation."""

from unittest.mock import MagicMock, patch

from healthcompass.rag import (
    STANDARD_REFUSAL,
    RAGPipeline,
    RAGResponse,
    check_faithfulness,
    check_retrieval_guardrails,
    condense_followup_question,
    format_citations,
    is_refusal,
)
from healthcompass.vector_store import RetrievalResult


def test_guardrails_refusal_when_no_chunks():
    guard = check_retrieval_guardrails([])
    assert guard.should_refuse is True
    assert guard.refusal_message == STANDARD_REFUSAL


def test_guardrails_refusal_when_distance_too_high():
    distant_chunk = RetrievalResult(
        rank=1, chunk_id="distant", distance=1.8, text="Irrelevant content", metadata={}
    )
    guard = check_retrieval_guardrails([distant_chunk], max_distance_threshold=1.2)
    assert guard.should_refuse is True


def test_guardrails_pass_with_close_chunk():
    close_chunk = RetrievalResult(
        rank=1, chunk_id="close", distance=0.25, text="Direct guidance", metadata={}
    )
    guard = check_retrieval_guardrails([close_chunk], max_distance_threshold=1.2)
    assert guard.should_refuse is False


def test_citations_extraction_and_mapping():
    sources = [
        {"rank": 1, "chunk_id": "c1", "source": "vaccine.pdf", "snippet": "Dose 1 is mandatory."},
        {"rank": 2, "chunk_id": "c2", "source": "fever.pdf", "snippet": "Fever isolation is 5 days."},
    ]
    answer = "Vaccination is required [1], while fever cases should isolate [2]."
    result = format_citations(answer, sources)

    assert len(result.citations) == 2
    assert result.cited_indices == [1, 2]
    assert result.citations[0].source == "vaccine.pdf"
    assert result.citations[1].source == "fever.pdf"


def test_citations_auto_append_when_missing():
    sources = [
        {"rank": 1, "chunk_id": "c1", "source": "vaccine.pdf", "snippet": "Mandatory booster."},
    ]
    answer = "Booster vaccination is strictly required for frontline healthcare workers."
    result = format_citations(answer, sources, auto_append_if_missing=True)

    assert "[1]" in result.text
    assert len(result.citations) == 1
    assert result.citations[0].chunk_id == "c1"


def test_is_refusal_detection():
    assert is_refusal("I do not have enough information in the provided context.") is True
    assert is_refusal("The mandatory isolation period in District A is 7 days.") is False


def test_check_faithfulness_score():
    context = "Isolation for acute respiratory infections in District A is 10 days."
    supported_answer = "District A requires 10 days isolation for infections."
    unsupported_answer = "Antibiotic prescription for pediatric hypertension."

    score_high = check_faithfulness(supported_answer, context)
    score_low = check_faithfulness(unsupported_answer, context)

    assert score_high > 0.6
    assert score_low < 0.3


def test_conversational_condensation_heuristic():
    history = [
        {"role": "user", "content": "What is the fever protocol in District A?"},
        {"role": "assistant", "content": "Patients should quarantine for 7 days."},
    ]
    followup = "What about for vaccinated contacts?"
    condensed = condense_followup_question(followup, history)

    assert "District A" in condensed or "fever" in condensed


def test_rag_pipeline_end_to_end_mock():
    mock_collection = MagicMock()
    pipeline = RAGPipeline(collection=mock_collection)

    mock_chunks = [
        RetrievalResult(
            rank=1,
            chunk_id="chunk_10",
            distance=0.15,
            text="District A protocol states isolation lasts 7 days for symptomatic cases.",
            metadata={"source": "district_a_guidelines.txt"},
        )
    ]

    with patch("healthcompass.rag.pipeline.retrieve", return_value=mock_chunks):
        response: RAGResponse = pipeline.run("What is the isolation duration in District A?")

        assert isinstance(response, RAGResponse)
        assert response.is_refusal is False
        assert response.chunks_used == 1
        assert len(response.citations) >= 1
        assert response.citations[0].source == "district_a_guidelines.txt"
        assert response.faithfulness_score > 0.0


def test_rag_pipeline_refusal_on_empty_retrieval():
    mock_collection = MagicMock()
    pipeline = RAGPipeline(collection=mock_collection)

    with patch("healthcompass.rag.pipeline.retrieve", return_value=[]):
        response: RAGResponse = pipeline.run("What is the policy for unknown condition X?")

        assert response.is_refusal is True
        assert STANDARD_REFUSAL in response.answer
        assert len(response.citations) == 0
