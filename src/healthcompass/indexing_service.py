"""Dedicated, canonical indexing service for HealthCompass guidance documents.

Unifies document loading, text cleaning, token-aware chunking, embedding generation,
ChromaDB vector indexing, and end-to-end verification.
"""

from __future__ import annotations

import json
import logging
import os
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from healthcompass.ingestion.basic_chunking import token_chunks
from healthcompass.ingestion.cleaning import clean_page
from healthcompass.ingestion.embeddings import generate_embeddings
from healthcompass.ingestion.indexing import index_embedded_chunks
from healthcompass.ingestion.loader import DocumentLoadError, load_document
from healthcompass.ingestion.metadata import tag_chunks
from healthcompass.providers import get_embedding_provider
from healthcompass.vector_store import (
    VectorStoreError,
    embed_query,
    initialize_vector_store,
)

logger = logging.getLogger("healthcompass.indexing")


class IndexingError(Exception):
    """Raised when guidance document indexing or verification fails."""

    pass


def delete_document_vectors(collection: Any, document_id: str) -> int:
    """Safely remove all vector records belonging to a specific document.

    Ensures re-indexing never leaves stale or duplicate chunks in ChromaDB.
    Never deletes the entire collection or unrelated documents.
    """
    try:
        existing = collection.get(where={"document_id": document_id})
        count = len(existing.get("ids", []))
        if count > 0:
            collection.delete(where={"document_id": document_id})
            logger.info(f"[Guidance] Removed {count} old vectors for document {document_id}")
            print(f"[Guidance] Removed {count} old vectors for document {document_id}")
        return count
    except Exception as e:
        logger.warning(f"[Guidance] delete_document_vectors notice: {e}")
        return 0


def verify_chroma_indexing(
    collection: Any,
    doc_id: str,
    doc_title: str,
    expected_chunk_count: int,
) -> None:
    """Verify that ChromaDB correctly stored and can retrieve document vectors.

    Validates:
    1. Chunks were generated.
    2. Embeddings were generated.
    3. Embedding count matches chunks.
    4. ChromaDB contains the vectors for this document.
    5. Stored metadata contains document identity.
    6. Stored metadata contains page information where available.
    7. A retrieval query against the collection can return the newly indexed document.
    """
    if expected_chunk_count <= 0:
        raise IndexingError(f"Verification failed: Expected chunk count must be > 0, got {expected_chunk_count}")

    # Check stored vectors for this document
    stored = collection.get(where={"document_id": doc_id}, include=["metadatas", "documents"])
    stored_ids = stored.get("ids", [])
    if len(stored_ids) != expected_chunk_count:
        raise IndexingError(
            f"Verification failed: ChromaDB contains {len(stored_ids)} vectors for document '{doc_id}', "
            f"expected {expected_chunk_count}."
        )

    # Check metadata integrity (document_id, page_number)
    metadatas = stored.get("metadatas", [])
    for meta in metadatas:
        if not meta or meta.get("document_id") != doc_id:
            raise IndexingError(f"Verification failed: Chunk metadata missing or incorrect document_id for '{doc_id}'.")
        if "page_number" not in meta:
            raise IndexingError(f"Verification failed: Chunk metadata missing page_number for '{doc_id}'.")

    # Check query retrieval using the configured embedding provider
    try:
        query_text = doc_title.strip() or "guidance directive protocol"
        query_vector = embed_query(query_text)
        query_results = collection.query(
            query_embeddings=[query_vector],
            n_results=min(3, max(collection.count(), 1)),
            where={"document_id": doc_id},
            include=["metadatas", "documents"],
        )
        returned_ids = query_results.get("ids", [[]])[0]
        if not returned_ids:
            raise IndexingError(f"Verification failed: Test query '{query_text}' returned no chunks for document '{doc_id}'.")
    except IndexingError:
        raise
    except Exception as e:
        raise IndexingError(f"Verification retrieval query failed: {e}") from e


def index_guidance_document(
    doc: Any,
    file_path: Path | str,
    collection: Optional[Any] = None,
) -> Any:
    """Canonical document indexing pipeline.

    Flow:
    PDF/file -> load_document -> clean_page -> token_chunks -> tag_chunks
    -> generate embeddings via configured provider -> ChromaDB upsert -> verify -> indexed.

    If any step fails:
    status = 'failed' with error_message stored, and IndexingError raised.
    """
    start_time = time.time()
    path = Path(file_path).expanduser().resolve()

    print(f"[Guidance] Starting indexing: {doc.filename}")
    logger.info(f"[Guidance] Starting indexing: {doc.filename}")

    if not path.exists() or not path.is_file():
        err_msg = f"Document file not found on disk: {path}"
        doc.status = "failed"
        doc.error_message = err_msg
        doc.updated_at = datetime.now(timezone.utc).isoformat()
        print(f"[Guidance] Indexing failed: {err_msg}")
        logger.error(f"[Guidance] Indexing failed: {err_msg}")
        raise IndexingError(err_msg)

    try:
        # 1. Load document pages with caller metadata
        metadata_map = {
            "document_id": str(doc.id),
            "document_title": str(doc.title),
            "category": str(doc.category),
            "region": str(doc.region),
            "authority": str(doc.authority),
            "version": str(doc.version),
        }

        try:
            pages = load_document(path, metadata=metadata_map)
        except DocumentLoadError as e:
            raise IndexingError(str(e)) from e

        if not pages or not any(p.text.strip() for p in pages):
            raise IndexingError("Document contains no extractable text; scanned PDFs require OCR.")

        print(f"[Guidance] Extracted pages: {len(pages)}")
        logger.info(f"[Guidance] Extracted pages: {len(pages)}")

        # 2. Clean, token-chunk, and tag with source metadata
        all_chunks: List[dict[str, Any]] = []
        for page in pages:
            cleaned = clean_page(page)
            if not cleaned.text.strip():
                continue

            tokenized = token_chunks(
                cleaned.text,
                source=cleaned.source,
                filename=cleaned.filename,
                size=400,
                overlap=60,
                metadata=cleaned.metadata,
            )

            tagged = tag_chunks(
                cleaned.filename,
                [chunk.text for chunk in tokenized],
                metadata={
                    **cleaned.metadata,
                    "document_id": str(doc.id),
                    "document_title": str(doc.title),
                    "page_number": str(cleaned.page_number or 1),
                    "category": str(doc.category),
                    "region": str(doc.region),
                    "authority": str(doc.authority),
                    "version": str(doc.version),
                },
            )

            # Build standardized chunk dictionaries with top-level keys for embedding generator
            for record, chunk in zip(tagged, tokenized, strict=True):
                chunk_meta = dict(record["metadata"])
                chunk_meta.update(
                    document_id=str(doc.id),
                    filename=str(doc.filename),
                    source=str(cleaned.source),
                    page_number=str(cleaned.page_number or 1),
                    chunk_id=str(chunk.chunk_id),
                    token_count=chunk.token_count,
                    title=str(doc.title),
                    version=str(doc.version),
                    authority=str(doc.authority),
                    category=str(doc.category),
                    region=str(doc.region),
                    status="indexed",
                )
                
                # Ensure source is not empty
                chunk_source = str(cleaned.source) if cleaned.source else str(doc.filename)
                if not chunk_source:
                    chunk_source = str(doc.filename)
                
                all_chunks.append({
                    "text": chunk.text,
                    "source": chunk_source,
                    "filename": str(doc.filename),
                    "chunk_id": chunk.chunk_id,
                    "metadata": chunk_meta,
                })

        if not all_chunks:
            raise IndexingError("Document produced no usable text chunks after cleaning and tokenization.")

        print(f"[Guidance] Generated chunks: {len(all_chunks)}")
        logger.info(f"[Guidance] Generated chunks: {len(all_chunks)}")

        # 3. Generate embeddings using configured provider abstraction
        print("[Guidance] Generating embeddings...")
        logger.info("[Guidance] Generating embeddings...")
        provider = get_embedding_provider()
        provider_name = os.getenv("EMBEDDING_PROVIDER", "local").lower()
        model_name = provider.get_model_name()
        expected_dim = provider.get_dimension()

        result, summary = generate_embeddings(all_chunks, skip_existing=False)

        if not result.embedded_chunks or len(result.embedded_chunks) != len(all_chunks):
            raise IndexingError(
                f"Embedding generation mismatch: expected {len(all_chunks)} embeddings, got {len(result.embedded_chunks)}."
            )

        print(f"[Guidance] Generated embeddings: {len(result.embedded_chunks)}")
        logger.info(f"[Guidance] Generated embeddings: {len(result.embedded_chunks)}")

        # Validate vector dimension
        vector_dim = len(result.embedded_chunks[0].embedding)
        if vector_dim != expected_dim:
            raise IndexingError(
                f"Embedding dimension mismatch: provider '{provider_name}' expected dimension {expected_dim}, "
                f"but generated {vector_dim}."
            )

        # 4. Upsert into ChromaDB
        print("[Guidance] Upserting into ChromaDB...")
        logger.info("[Guidance] Upserting into ChromaDB...")
        if collection is None:
            collection = initialize_vector_store()

        # Validate collection dimension compatibility
        coll_dim = (collection.metadata or {}).get("embedding_dimension")
        if coll_dim is not None and coll_dim != vector_dim:
            raise VectorStoreError(
                f"ChromaDB collection dimension mismatch: collection '{collection.name}' expects dimension {coll_dim}, "
                f"but incoming vectors have dimension {vector_dim}. Do not mix embedding spaces."
            )

        # Remove existing vectors for this document to prevent duplicates
        delete_document_vectors(collection, doc.id)

        # Batch upsert new chunks
        upsert_res = index_embedded_chunks(collection, result.embedded_chunks)
        if upsert_res.failures:
            first_err = upsert_res.failures[0].get("error", "Unknown upsert error")
            raise VectorStoreError(f"ChromaDB batch upsert failed: {first_err}")

        print(f"[Guidance] Indexed vectors: {len(result.embedded_chunks)}")
        logger.info(f"[Guidance] Indexed vectors: {len(result.embedded_chunks)}")

        # 5. Verification
        verify_chroma_indexing(
            collection=collection,
            doc_id=doc.id,
            doc_title=doc.title,
            expected_chunk_count=len(result.embedded_chunks),
        )
        print("[Guidance] Verification successful")
        logger.info("[Guidance] Verification successful")

        # 6. Update document state
        elapsed_ms = (time.time() - start_time) * 1000.0
        doc.status = "indexed"
        doc.chunk_count = len(result.embedded_chunks)
        doc.page_count = max(len(pages), 1)
        doc.embedding_provider = provider_name
        if hasattr(doc, "embedding_model"):
            doc.embedding_model = model_name
        if hasattr(doc, "vector_dimension"):
            doc.vector_dimension = vector_dim
        if hasattr(doc, "indexed_at"):
            doc.indexed_at = datetime.now(timezone.utc).isoformat()
        if hasattr(doc, "processing_time_ms"):
            doc.processing_time_ms = round(elapsed_ms, 2)
        doc.error_message = None
        doc.updated_at = datetime.now(timezone.utc).isoformat()

        print(f"[Guidance] Document indexed successfully: {doc.title} ({doc.chunk_count} chunks in {round(elapsed_ms, 1)}ms)")
        logger.info(f"[Guidance] Document indexed successfully: {doc.title}")
        return doc

    except Exception as e:
        safe_err = str(e) or "An error occurred during document indexing."
        doc.status = "failed"
        doc.error_message = safe_err
        doc.updated_at = datetime.now(timezone.utc).isoformat()
        print(f"[Guidance] Indexing failed: {safe_err}")
        logger.error(f"[Guidance] Indexing failed: {safe_err}")
        traceback.print_exc()
        raise IndexingError(safe_err) from e
