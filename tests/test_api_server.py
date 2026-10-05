"""Unit and integration tests for HealthCompass API server."""

import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api_server import app
from healthcompass.rag import Citation, RAGResponse


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ask_endpoint_success(client):
    mock_rag_response = RAGResponse(
        question="What is the isolation protocol?",
        condensed_query="What is the isolation protocol?",
        answer="Isolation period is 7 days in District A [1].",
        citations=[
            Citation(
                index=1,
                chunk_id="chunk_1",
                source="guidance.pdf",
                section="Section 1",
                snippet="Isolation period is 7 days",
                distance=0.15,
            )
        ],
        sources=[{"chunk_id": "chunk_1", "source": "guidance.pdf", "rank": 1, "distance": 0.15}],
        context_tokens=100,
        chunks_retrieved=3,
        chunks_used=1,
        is_refusal=False,
        latency_ms=25.0,
        faithfulness_score=0.95,
    )

    with patch("api_server.rag_pipeline.run", return_value=mock_rag_response):
        response = client.post("/ask", json={"question": "What is the isolation protocol?"})
        assert response.status_code == 200
        data = response.json()
        assert "Isolation period is 7 days" in data["answer"]
        assert len(data["citations"]) == 1
        assert data["citations"][0]["source"] == "guidance.pdf"
        assert data["faithfulness_score"] == 0.95
        assert data["cached"] is False


def test_ask_endpoint_caching(client):
    mock_rag_response = RAGResponse(
        question="Cached query test",
        condensed_query="Cached query test",
        answer="Cached answer.",
        citations=[],
        sources=[],
        context_tokens=50,
        chunks_retrieved=1,
        chunks_used=1,
        is_refusal=False,
        latency_ms=10.0,
        faithfulness_score=1.0,
    )

    with patch("api_server.rag_pipeline.run", return_value=mock_rag_response):
        # First call: populates cache
        res1 = client.post("/ask", json={"question": "Cached query test"})
        assert res1.status_code == 200
        assert res1.json()["cached"] is False

        # Second call: served from cache
        res2 = client.post("/ask", json={"question": "Cached query test"})
        assert res2.status_code == 200
        assert res2.json()["cached"] is True


def test_ask_stream_endpoint(client):
    with patch("api_server.rag_pipeline.run_stream", return_value=iter(["Hello", " ", "World"])):
        response = client.post("/ask/stream", json={"question": "Stream test"})
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        body = response.text
        assert "Hello" in body
        assert "World" in body


def test_document_upload_endpoint(client):
    fake_file_content = b"Official guidance on emergency vaccination procedures in District A."
    file = io.BytesIO(fake_file_content)

    mock_result = MagicMock(inserted_count=1)
    with patch("api_server.upsert_records", return_value=mock_result):
        response = client.post(
            "/documents/upload",
            files={"file": ("emergency_vaccine.txt", file, "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["chunks_indexed"] == 1


def test_usage_stats_endpoint(client):
    response = client.get("/stats/usage")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "cache_hit_rate" in data
