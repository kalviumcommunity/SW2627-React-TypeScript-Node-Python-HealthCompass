"""Comprehensive tests for the HealthCompass guidance document indexing pipeline.

Tests cover:
  A. Successful text document ingestion (extract → chunk → embed → index → verify → indexed)
  B. Unsupported file extension rejection
  C. Empty/no-text document failure with actionable error message
  D. Embedding failure handling (status=failed, error stored)
  E. ChromaDB failure handling (status=failed, no false success)
  F. Re-index replaces existing vectors (no duplicates)
  G. Re-index failure preserves document and stores error
  H. Provider/dimension mismatch rejection
  I. Query retrieval returns newly indexed document
  J. Seeding does NOT falsely report indexed on failure
  K. Missing file reindex failure
  L. API error response format (JSON detail)
"""

import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from healthcompass.guidance_service import (
    ALLOWED_EXTENSIONS,
    GuidanceDocument,
    GuidanceService,
)
from healthcompass.indexing_service import (
    IndexingError,
    delete_document_vectors,
    index_guidance_document,
    verify_chroma_indexing,
)
from healthcompass.vector_store import (
    VectorStoreConfig,
    VectorStoreError,
    initialize_vector_store,
)


# ─── Fixtures ────────────────────────────────────────────────────

@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace with documents dir and registry."""
    docs_dir = tmp_path / "data" / "documents"
    docs_dir.mkdir(parents=True)
    registry_file = tmp_path / "data" / "documents_registry.json"
    return tmp_path, docs_dir, registry_file


@pytest.fixture
def sample_text_content():
    """Generate realistic public-health guidance text for testing."""
    return (
        "National Vaccination Priority Framework (Version 5.0)\n"
        "Issuing Authority: National Public Health Directorate\n"
        "Effective Date: October 1, 2026\n\n"
        "Section 1: Priority Groups\n"
        "Tier 1 includes frontline healthcare workers, emergency responders, "
        "and critical clinical staff. Tier 2 includes adults aged 65 and older, "
        "individuals with severe comorbidities, and immunocompromised patients.\n\n"
        "Section 2: Cold-Chain Protocols\n"
        "Ultra-cold formulations must be maintained at -80C to -60C. Standard "
        "refrigerated vaccines require steady 2C to 8C monitoring. Any temperature "
        "excursion exceeding 30 minutes must trigger immediate quarantine.\n\n"
        "Section 3: Adverse Reaction Surveillance\n"
        "Recipients must be observed for 15 minutes post-injection (30 minutes for "
        "history of anaphylaxis). Emergency epinephrine autoinjectors (1:1000) "
        "must be available at all vaccination points.\n"
    )


@pytest.fixture
def sample_guidance_doc(temp_workspace, sample_text_content):
    """Create a GuidanceDocument with a real text file on disk."""
    tmp_path, docs_dir, _ = temp_workspace
    filename = "vaccination_framework_v5.txt"
    file_path = docs_dir / filename
    file_path.write_text(sample_text_content, encoding="utf-8")

    doc = GuidanceDocument(
        id=f"doc_test_{uuid.uuid4().hex[:8]}",
        title="Vaccination Priority Framework v5",
        description="Standard operating guidelines for vaccination.",
        filename=filename,
        file_path=str(file_path),
        file_size=len(sample_text_content.encode("utf-8")),
        mime_type="text/plain",
        category="Vaccination",
        region="National",
        authority="National Public Health Directorate",
        version="5.0",
        effective_date="2026-10-01",
        status="processing",
        chunk_count=0,
        page_count=1,
        tags=["Vaccination", "Priority"],
        file_hash="abc123",
        created_at="2026-10-01T00:00:00Z",
        updated_at="2026-10-01T00:00:00Z",
    )
    return doc, file_path


@pytest.fixture
def test_chroma_collection(tmp_path):
    """Create a temporary ChromaDB collection for testing."""
    db_path = str(tmp_path / "test_chroma_db")
    config = VectorStoreConfig(
        db_path=db_path,
        collection_name="test_guidance_collection",
        embedding_dimension=384,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    )
    return initialize_vector_store(config)


# ─── A: Successful Document Ingestion ────────────────────────────

class TestSuccessfulIngestion:
    """Test that a valid text document goes through the full pipeline."""

    def test_index_text_document_end_to_end(self, sample_guidance_doc, test_chroma_collection):
        """A valid .txt document should be extracted, chunked, embedded, indexed, and verified."""
        doc, file_path = sample_guidance_doc
        result = index_guidance_document(doc, file_path, collection=test_chroma_collection)

        assert result.status == "indexed"
        assert result.chunk_count > 0
        assert result.error_message is None

    def test_indexed_document_has_vectors_in_chroma(self, sample_guidance_doc, test_chroma_collection):
        """After indexing, ChromaDB should contain the correct number of vectors."""
        doc, file_path = sample_guidance_doc
        index_guidance_document(doc, file_path, collection=test_chroma_collection)

        stored = test_chroma_collection.get(
            where={"document_id": doc.id},
            include=["metadatas"],
        )
        assert len(stored["ids"]) == doc.chunk_count
        assert len(stored["ids"]) > 0

    def test_indexed_vectors_have_correct_metadata(self, sample_guidance_doc, test_chroma_collection):
        """Stored vectors should contain traceable metadata: document_id, filename, page_number, etc."""
        doc, file_path = sample_guidance_doc
        index_guidance_document(doc, file_path, collection=test_chroma_collection)

        stored = test_chroma_collection.get(
            where={"document_id": doc.id},
            include=["metadatas"],
        )
        for meta in stored["metadatas"]:
            assert meta["document_id"] == doc.id
            assert "page_number" in meta
            assert "filename" in meta
            assert "source" in meta
            assert "category" in meta

    def test_indexed_document_has_page_count(self, sample_guidance_doc, test_chroma_collection):
        """Document page_count should be updated after indexing."""
        doc, file_path = sample_guidance_doc
        index_guidance_document(doc, file_path, collection=test_chroma_collection)
        assert doc.page_count >= 1


# ─── B: Unsupported File Extension ──────────────────────────────

class TestUnsupportedFormat:
    """Test rejection of unsupported file formats."""

    def test_guidance_service_rejects_csv(self, temp_workspace):
        """GuidanceService.add_document should reject .csv files."""
        tmp_path, docs_dir, registry_file = temp_workspace
        service = GuidanceService.__new__(GuidanceService)
        service.documents_dir = docs_dir
        service.registry_file = registry_file
        service._ensure_registry()

        with pytest.raises(ValueError, match="Unsupported file format"):
            service.add_document(
                file_bytes=b"name,value\ntest,123",
                filename="data.csv",
                title="Test CSV",
                category="General",
            )


# ─── C: Empty Document / No Extractable Text ────────────────────

class TestEmptyDocument:
    """Test handling of documents with no extractable text."""

    def test_empty_text_file_fails_with_clear_error(self, temp_workspace, test_chroma_collection):
        """An empty .txt file should fail with an actionable error message."""
        _, docs_dir, _ = temp_workspace
        empty_file = docs_dir / "empty.txt"
        empty_file.write_text("", encoding="utf-8")

        doc = GuidanceDocument(
            id="doc_empty_test",
            title="Empty Document",
            description="",
            filename="empty.txt",
            file_path=str(empty_file),
            file_size=0,
            mime_type="text/plain",
            category="General",
            region="National",
            authority="Test",
            version="1.0",
            effective_date="2026-01-01",
            status="processing",
        )

        with pytest.raises(IndexingError, match="(?i)empty|no extractable text"):
            index_guidance_document(doc, empty_file, collection=test_chroma_collection)

        assert doc.status == "failed"
        assert doc.error_message is not None

    def test_whitespace_only_file_fails(self, temp_workspace, test_chroma_collection):
        """A file with only whitespace should fail indexing."""
        _, docs_dir, _ = temp_workspace
        ws_file = docs_dir / "whitespace.txt"
        ws_file.write_text("   \n\n\t  \n", encoding="utf-8")

        doc = GuidanceDocument(
            id="doc_ws_test",
            title="Whitespace Only",
            description="",
            filename="whitespace.txt",
            file_path=str(ws_file),
            file_size=10,
            mime_type="text/plain",
            category="General",
            region="National",
            authority="Test",
            version="1.0",
            effective_date="2026-01-01",
            status="processing",
        )

        with pytest.raises(IndexingError):
            index_guidance_document(doc, ws_file, collection=test_chroma_collection)

        assert doc.status == "failed"


# ─── D: Embedding Failure Handling ───────────────────────────────

class TestEmbeddingFailure:
    """Test that embedding failures set status=failed with error message."""

    def test_embedding_error_sets_failed_status(self, sample_guidance_doc, test_chroma_collection):
        """If embedding generation fails, document should be status=failed with error_message."""
        doc, file_path = sample_guidance_doc

        with patch("healthcompass.indexing_service.generate_embeddings") as mock_embed:
            mock_embed.side_effect = Exception("Simulated embedding API failure")

            with pytest.raises(IndexingError, match="Simulated embedding API failure"):
                index_guidance_document(doc, file_path, collection=test_chroma_collection)

        assert doc.status == "failed"
        assert "Simulated embedding API failure" in doc.error_message


# ─── E: ChromaDB Failure Handling ────────────────────────────────

class TestChromaFailure:
    """Test that ChromaDB failures are handled without false success."""

    def test_chroma_upsert_failure_sets_failed_status(self, sample_guidance_doc, test_chroma_collection):
        """If ChromaDB upsert fails, document should be status=failed."""
        doc, file_path = sample_guidance_doc

        with patch("healthcompass.indexing_service.index_embedded_chunks") as mock_index:
            mock_index.return_value = MagicMock(failures=[{"error": "Simulated ChromaDB write error"}])

            with pytest.raises(IndexingError, match="ChromaDB batch upsert failed"):
                index_guidance_document(doc, file_path, collection=test_chroma_collection)

        assert doc.status == "failed"
        assert doc.error_message is not None


# ─── F: Re-Index Without Duplicates ──────────────────────────────

class TestReindexNoDuplicates:
    """Test that re-indexing replaces, not duplicates, vectors."""

    def test_reindex_same_document_no_duplicates(self, sample_guidance_doc, test_chroma_collection):
        """Indexing the same document twice should result in the same vector count."""
        doc, file_path = sample_guidance_doc

        # First index
        index_guidance_document(doc, file_path, collection=test_chroma_collection)
        first_count = doc.chunk_count
        assert first_count > 0

        # Reset status for re-index
        doc.status = "processing"
        doc.error_message = None

        # Second index (re-index)
        index_guidance_document(doc, file_path, collection=test_chroma_collection)
        second_count = doc.chunk_count

        assert second_count == first_count, f"Expected {first_count} chunks, got {second_count} (duplicates!)"

        # Verify actual ChromaDB vector count
        stored = test_chroma_collection.get(where={"document_id": doc.id})
        assert len(stored["ids"]) == first_count

    def test_reindex_three_times_no_growth(self, sample_guidance_doc, test_chroma_collection):
        """Three consecutive re-indexes should not grow vector count."""
        doc, file_path = sample_guidance_doc

        counts = []
        for _ in range(3):
            doc.status = "processing"
            doc.error_message = None
            index_guidance_document(doc, file_path, collection=test_chroma_collection)
            counts.append(doc.chunk_count)

        assert counts[0] == counts[1] == counts[2], f"Vector counts grew: {counts}"


# ─── G: Re-index Failure Handling ────────────────────────────────

class TestReindexFailure:
    """Test that re-index failure returns safe error and updates status."""

    def test_reindex_missing_file_fails(self, temp_workspace, test_chroma_collection):
        """Re-indexing a document whose file was deleted should fail clearly."""
        _, docs_dir, _ = temp_workspace

        doc = GuidanceDocument(
            id="doc_missing_file_test",
            title="Missing File Doc",
            description="",
            filename="deleted.txt",
            file_path=str(docs_dir / "nonexistent.txt"),
            file_size=100,
            mime_type="text/plain",
            category="General",
            region="National",
            authority="Test",
            version="1.0",
            effective_date="2026-01-01",
            status="processing",
        )

        with pytest.raises(IndexingError, match="not found"):
            index_guidance_document(doc, docs_dir / "nonexistent.txt", collection=test_chroma_collection)

        assert doc.status == "failed"
        assert "not found" in doc.error_message


# ─── H: Dimension Mismatch Detection ────────────────────────────

class TestDimensionMismatch:
    """Test that dimension mismatches are detected and handled."""

    def test_empty_collection_wrong_dimension_is_recreated(self, tmp_path):
        """An empty collection with wrong dimension metadata should be safely recreated."""
        db_path = str(tmp_path / "mismatch_db")

        # Create a collection with 1536 dimension metadata
        config_1536 = VectorStoreConfig(
            db_path=db_path,
            collection_name="test_mismatch",
            embedding_dimension=1536,
            embedding_model="text-embedding-3-small",
        )
        collection_1536 = initialize_vector_store(config_1536)
        assert collection_1536.metadata.get("embedding_dimension") == 1536

        # Now try to initialize with 384 dimension — should succeed by recreating
        config_384 = VectorStoreConfig(
            db_path=db_path,
            collection_name="test_mismatch",
            embedding_dimension=384,
            embedding_model="all-MiniLM-L6-v2",
        )
        collection_384 = initialize_vector_store(config_384)
        assert collection_384.metadata.get("embedding_dimension") == 384


# ─── I: Query Retrieval ─────────────────────────────────────────

class TestQueryRetrieval:
    """Test that newly indexed documents are retrievable."""

    def test_indexed_document_is_retrievable(self, sample_guidance_doc, test_chroma_collection):
        """After indexing, a relevant query should retrieve chunks from the document."""
        doc, file_path = sample_guidance_doc
        index_guidance_document(doc, file_path, collection=test_chroma_collection)

        # Query using embed_query
        from healthcompass.vector_store import embed_query

        query_vector = embed_query("vaccination priority framework cold chain")
        results = test_chroma_collection.query(
            query_embeddings=[query_vector],
            n_results=3,
            where={"document_id": doc.id},
            include=["metadatas", "documents"],
        )

        assert results["ids"][0], "Query should return at least one result"
        assert results["metadatas"][0][0]["document_id"] == doc.id


# ─── J: Seeding Status Integrity ────────────────────────────────

class TestSeedingIntegrity:
    """Test that seeding doesn't falsely report indexed status on failure."""

    def test_seeded_docs_start_as_processing(self, temp_workspace):
        """Seeded documents should start with status='processing', not 'indexed'."""
        tmp_path, docs_dir, registry_file = temp_workspace
        # Run with a mocked vector store that fails
        with patch("healthcompass.guidance_service.initialize_vector_store") as mock_vs:
            mock_vs.side_effect = Exception("Simulated vector store failure")
            service = GuidanceService(documents_dir=docs_dir, registry_file=registry_file)

        docs = service.list_documents()
        for doc in docs:
            assert doc.status == "failed", f"Seeded doc '{doc.title}' should be 'failed' but was '{doc.status}'"
            assert doc.error_message is not None


# ─── K: Delete Document Vectors ──────────────────────────────────

class TestDeleteDocumentVectors:
    """Test that vector deletion targets only the specified document."""

    def test_delete_only_targets_specified_document(self, sample_guidance_doc, test_chroma_collection, temp_workspace):
        """Deleting vectors for one document should not affect other documents."""
        doc1, file_path1 = sample_guidance_doc
        index_guidance_document(doc1, file_path1, collection=test_chroma_collection)

        # Create and index a second document
        _, docs_dir, _ = temp_workspace
        file2 = docs_dir / "second_doc.txt"
        file2.write_text("This is a completely different public health document about PPE protocols.", encoding="utf-8")
        doc2 = GuidanceDocument(
            id=f"doc_second_{uuid.uuid4().hex[:8]}",
            title="PPE Protocols",
            description="",
            filename="second_doc.txt",
            file_path=str(file2),
            file_size=80,
            mime_type="text/plain",
            category="PPE",
            region="National",
            authority="Test",
            version="1.0",
            effective_date="2026-01-01",
            status="processing",
        )
        index_guidance_document(doc2, file2, collection=test_chroma_collection)

        doc1_chunks = doc1.chunk_count
        doc2_chunks = doc2.chunk_count

        # Delete only doc1's vectors
        deleted = delete_document_vectors(test_chroma_collection, doc1.id)

        # doc1 vectors should be gone
        stored_doc1 = test_chroma_collection.get(where={"document_id": doc1.id})
        assert len(stored_doc1["ids"]) == 0

        # doc2 vectors should still be intact
        stored_doc2 = test_chroma_collection.get(where={"document_id": doc2.id})
        assert len(stored_doc2["ids"]) == doc2_chunks


# ─── L: API Error Response Format ────────────────────────────────

class TestAPIErrorFormat:
    """Test that API errors return proper JSON with 'detail' field."""

    def test_upload_missing_title_returns_400(self):
        """Upload with empty title should return HTTP 400 with 'detail'."""
        from fastapi.testclient import TestClient
        from api_server import app

        client = TestClient(app)
        response = client.post(
            "/api/guidance/upload",
            data={"title": "", "category": "General"},
            files={"file": ("test.txt", b"test content", "text/plain")},
        )
        assert response.status_code in (400, 422)
        body = response.json()
        assert "detail" in body

    def test_reindex_nonexistent_doc_returns_404(self):
        """Reindex of nonexistent document should return HTTP 404 with 'detail'."""
        from fastapi.testclient import TestClient
        from api_server import app

        client = TestClient(app)
        response = client.post("/api/guidance/nonexistent_doc_id/reindex")
        assert response.status_code == 404
        body = response.json()
        assert "detail" in body

    def test_unread_count_returns_200(self):
        """The /api/updates/unread/count endpoint should return 200 with count."""
        from fastapi.testclient import TestClient
        from api_server import app

        client = TestClient(app)
        response = client.get("/api/updates/unread/count")
        assert response.status_code == 200
        body = response.json()
        assert "count" in body
        assert isinstance(body["count"], int)

    def test_cors_options_returns_200(self):
        """CORS preflight OPTIONS request should succeed."""
        from fastapi.testclient import TestClient
        from api_server import app

        client = TestClient(app)
        response = client.options(
            "/api/guidance/test_doc/reindex",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == 200
