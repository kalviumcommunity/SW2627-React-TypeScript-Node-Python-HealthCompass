"""Unit tests for RAG evaluation module."""

from unittest.mock import MagicMock

from evaluation.evaluate_rag import evaluate_rag_pipeline, generate_markdown_report
from healthcompass.rag import Citation, RAGPipeline, RAGResponse


def test_evaluate_rag_pipeline_with_mock():
    mock_pipeline = MagicMock(spec=RAGPipeline)

    def mock_run(query: str):
        if "alien" in query.lower() or "building" in query.lower():
            return RAGResponse(
                question=query,
                condensed_query=query,
                answer="I do not have enough verified information in the official guidance to answer this question.",
                citations=[],
                sources=[],
                context_tokens=0,
                chunks_retrieved=0,
                chunks_used=0,
                is_refusal=True,
                latency_ms=15.0,
                faithfulness_score=1.0,
            )
        return RAGResponse(
            question=query,
            condensed_query=query,
            answer="Vaccination guidance prioritizes healthcare workers and vulnerable individuals [1].",
            citations=[
                Citation(
                    index=1,
                    chunk_id="v1",
                    source="vaccination_guidance.txt",
                    section="Priority Groups",
                    snippet="Healthcare workers first",
                    distance=0.1,
                )
            ],
            sources=[{"source": "vaccination_guidance.txt"}],
            context_tokens=150,
            chunks_retrieved=3,
            chunks_used=1,
            is_refusal=False,
            latency_ms=45.0,
            faithfulness_score=0.92,
        )

    mock_pipeline.run.side_effect = mock_run

    summary, results = evaluate_rag_pipeline(mock_pipeline)

    assert summary.total_queries == 5
    assert summary.refusal_accuracy == 1.0
    assert summary.citation_accuracy == 1.0
    assert summary.average_groundedness > 0.8
    assert len(results) == 5

    report = generate_markdown_report(summary, results)
    assert "# 🧭 HealthCompass RAG Pipeline Evaluation Report" in report
    assert "**Refusal Accuracy**: 100.0%" in report
