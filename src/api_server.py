"""FastAPI server for HealthCompass RAG application, Guidance Library, and Dashboard."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, List, Optional

# Ensure src/ is on sys.path for direct module imports
src_dir = str(Path(__file__).resolve().parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from healthcompass.dashboard_service import DashboardResponse, DashboardService
from healthcompass.guidance_service import GuidanceDocument, GuidanceService
from healthcompass.providers import get_chat_provider
from healthcompass.rag import build_augmented_prompt
from healthcompass.vector_store import (
    RetrievalResult,
    VectorRecord,
    initialize_vector_store,
    retrieve,
)

load_dotenv()

app = FastAPI(
    title="HealthCompass API",
    version="2.0.0",
    description="Public Health Guidance Intelligence & RAG Operations Platform",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

guidance_service = GuidanceService()
dashboard_service = DashboardService(guidance_service=guidance_service)


# ─── Pydantic Models ─────────────────────────────────────────────────


class AskRequest(BaseModel):
    """Request model for ask endpoint."""

    question: str
    document_id: Optional[str] = None
    top_k: int = 5


class SourceInfo(BaseModel):
    """Source information from retrieval."""

    chunk_id: str
    source: str
    chunk_index: str
    rank: int
    distance: float
    excerpt: str = ""
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    page_number: Optional[str] = None
    authority: Optional[str] = None
    version: Optional[str] = None
    relevance_score: Optional[float] = None


class AskResponse(BaseModel):
    """Response model for ask endpoint."""

    answer: str
    sources: List[SourceInfo]
    context_tokens: int
    chunks_used: int
    document_scope: Optional[str] = None


class GuidanceUploadResponse(BaseModel):
    """Response returned when a document is uploaded and indexed."""

    success: bool
    message: str
    document_id: Optional[str] = None
    status: Optional[str] = None
    chunk_count: Optional[int] = None
    chunks_indexed: int = 0
    document: Optional[dict[str, Any]] = None
    detail: Optional[str] = None


class AlertItem(BaseModel):
    id: str
    severity: str
    topic: str
    location: Optional[str]
    date: str
    description: str
    status: str


class UpdateItem(BaseModel):
    id: str
    title: str
    category: str
    date: str
    summary: str
    importance: str


SAMPLE_ALERTS = [
    AlertItem(
        id="1",
        severity="Critical",
        topic="Nipah Virus Outbreak",
        location="District A",
        date="2026-09-01",
        description="Confirmed positive case in sector 4. Enhanced barrier nursing and Tier-2 PPE active.",
        status="Active",
    ),
    AlertItem(
        id="2",
        severity="Warning",
        topic="Vaccine Cold Chain Disruption",
        location="North Sector",
        date="2026-09-02",
        description="Power outage affected sub-depot storage. Re-testing batch potency.",
        status="Investigating",
    ),
]

SAMPLE_UPDATES = [
    UpdateItem(
        id="1",
        title="Vaccination Priority Framework Revision",
        category="Vaccination",
        date="2026-08-15",
        summary="Updated Tier-1 priority list to include all clinical triage personnel.",
        importance="High",
    ),
    UpdateItem(
        id="2",
        title="Field Infection Control SOP v2.0",
        category="Infection Control",
        date="2026-07-20",
        summary="Mandatory double-gloving protocol for viral hemorrhagic/respiratory intake.",
        importance="Routine",
    ),
]


# ─── System & Health Endpoints ───────────────────────────────────────


@app.get("/health")
def health_check():
    """Health check endpoint indicating RAG system status."""
    return {
        "status": "healthy",
        "chat_provider": os.getenv("CHAT_PROVIDER", "groq"),
        "embedding_provider": os.getenv("EMBEDDING_PROVIDER", "local"),
        "chat_model": os.getenv("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile"),
        "embedding_model": os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        "total_guidance_documents": len(guidance_service.list_documents()),
    }


# ─── Dashboard Endpoints ─────────────────────────────────────────────


@app.get("/api/dashboard")
@app.get("/dashboard")
def get_dashboard():
    """Get complete dashboard operational metrics, directives, surveillance trends, and activity."""
    return dashboard_service.get_dashboard().to_dict()


@app.get("/stats")
def get_stats():
    """Legacy dashboard statistics with contextual subtitles."""
    docs = guidance_service.list_documents()
    active_alerts_count = len(SAMPLE_ALERTS)
    critical_alerts = sum(1 for a in SAMPLE_ALERTS if a.severity.lower() == "critical")
    return {
        "active_alerts": active_alerts_count,
        "active_alerts_subtitle": f"{critical_alerts} critical" if critical_alerts else "All stable",
        "new_guidance": len(docs),
        "new_guidance_subtitle": f"{len(docs)} active in library",
        "policy_updates": len(SAMPLE_UPDATES),
        "policy_updates_subtitle": "Latest v4.2",
        "saved_guidance": 8,
        "saved_guidance_subtitle": "Frequently used",
    }


@app.get("/alerts", response_model=List[AlertItem])
def get_alerts():
    """Get active alerts."""
    return SAMPLE_ALERTS


@app.get("/updates", response_model=List[UpdateItem])
def get_updates():
    """Get recent policy updates."""
    return SAMPLE_UPDATES


# ─── Guidance Library Endpoints ──────────────────────────────────────


@app.get("/api/guidance")
@app.get("/guidance")
def get_guidance(
    search: Optional[str] = Query(None, description="Search query across title, description, authority, tags"),
    status: Optional[str] = Query(None, description="Filter by document status: active, processing, archived, failed"),
    category: Optional[str] = Query(None, description="Filter by category: Outbreak, Vaccination, PPE, Emergency, etc."),
    region: Optional[str] = Query(None, description="Filter by region: National, District A, etc."),
):
    """Get list of guidance documents matching filters."""
    docs = guidance_service.list_documents(
        search=search,
        status=status,
        category=category,
        region=region,
    )
    return [d.to_dict() for d in docs]


@app.get("/guidance/search")
def search_guidance(query: str):
    """Search guidance documents by topic or title (compatibility endpoint)."""
    docs = guidance_service.list_documents(search=query)
    return [d.to_dict() for d in docs]


@app.get("/api/guidance/{document_id}")
@app.get("/guidance/{document_id}")
def get_guidance_by_id(document_id: str):
    """Get single guidance document metadata."""
    doc = guidance_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Guidance document '{document_id}' not found.")
    return doc.to_dict()


@app.get("/api/guidance/{document_id}/file")
@app.get("/guidance/{document_id}/file")
def get_guidance_file(document_id: str):
    """Safely stream the uploaded guidance document file for in-browser PDF/text preview."""
    doc = guidance_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Guidance document not found.")

    file_path = Path(doc.file_path).resolve()
    # Path traversal protection: ensure file resides inside data/documents
    base_dir = Path("data/documents").resolve()
    try:
        file_path.relative_to(base_dir)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: invalid file path.")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document file not found on disk.")

    media_type = doc.mime_type or "application/octet-stream"
    if file_path.suffix.lower() == ".pdf":
        media_type = "application/pdf"
    elif file_path.suffix.lower() in {".txt", ".md"}:
        media_type = "text/plain; charset=utf-8"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=doc.filename,
        content_disposition_type="inline",
    )


@app.post("/api/guidance/upload", response_model=GuidanceUploadResponse)
@app.post("/guidance/upload", response_model=GuidanceUploadResponse)
async def upload_guidance(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(...),
    description: str = Form(""),
    region: str = Form("National"),
    authority: str = Form("National Public Health Authority"),
    version: str = Form("1.0"),
    effective_date: str = Form(""),
    tags: str = Form(""),
):
    """Upload an official health guidance document (PDF, TXT, MD), process, and index it into ChromaDB."""
    try:
        if not title or not title.strip():
            raise HTTPException(status_code=400, detail="Document title is required.")
        if not category or not category.strip():
            raise HTTPException(status_code=400, detail="Category is required.")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        filename = file.filename or "uploaded_guidance.pdf"
        from healthcompass.guidance_service import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES

        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{suffix}'. Supported formats are: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
            )

        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        doc = guidance_service.add_document(
            file_bytes=content,
            filename=filename,
            title=title.strip(),
            category=category.strip(),
            description=description.strip(),
            region=region.strip() if region else "National",
            authority=authority.strip() if authority else "National Public Health Authority",
            version=version.strip() if version else "1.0",
            effective_date=effective_date.strip() if effective_date else "",
            tags=tag_list,
        )

        if doc.status == "failed":
            raise HTTPException(
                status_code=400,
                detail=doc.error_message or "Failed to process and index document.",
            )

        return GuidanceUploadResponse(
            success=True,
            message=f"Guidance document '{doc.title}' uploaded and indexed successfully with {doc.chunk_count} knowledge chunks.",
            document_id=doc.id,
            status=doc.status,
            chunk_count=doc.chunk_count,
            chunks_indexed=doc.chunk_count,
            document=doc.to_dict(),
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process and index document: {e}")


@app.post("/api/guidance/{document_id}/archive")
@app.post("/guidance/{document_id}/archive")
def archive_guidance(document_id: str):
    """Archive a guidance document."""
    doc = guidance_service.archive_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"success": True, "message": f"Document '{doc.title}' archived.", "document": doc.to_dict()}


@app.post("/api/guidance/{document_id}/reindex")
@app.post("/guidance/{document_id}/reindex")
def reindex_guidance(document_id: str):
    """Re-index an existing guidance document."""
    try:
        doc = guidance_service.reindex_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        if doc.status == "failed":
            raise HTTPException(
                status_code=400,
                detail=doc.error_message or "Document re-indexing failed.",
            )
        return {
            "success": True,
            "message": f"Document '{doc.title}' re-indexed with {doc.chunk_count} chunks.",
            "document_id": doc.id,
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "document": doc.to_dict(),
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to re-index document: {e}")


# ─── Ask HealthCompass RAG Endpoint ──────────────────────────────────


@app.post("/api/ask", response_model=AskResponse)
@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """Ask HealthCompass a question using the RAG pipeline.

    Optionally filters retrieval to a specific document when request.document_id is provided.
    """
    try:
        # 1. Initialize vector collection
        collection = initialize_vector_store()

        # If provider-specific collection has 0 items, check fallback collections
        if collection.count() == 0:
            try:
                import chromadb
                db_path = os.getenv("CHROMA_DB_PATH", "data/chroma_db")
                client = chromadb.PersistentClient(path=db_path)
                for col_name in ["healthcompass_documents", "healthcompass_documents_local"]:
                    try:
                        c = client.get_collection(col_name)
                        if c.count() > 0:
                            collection = c
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        if collection.count() == 0:
            return AskResponse(
                answer=(
                    "### No Guidance Documents Indexed\n\n"
                    "The HealthCompass knowledge base is currently empty. "
                    "Please navigate to the **Guidance Library** and click **+ Add Guidance** to upload and index official clinical protocols and directives."
                ),
                sources=[],
                context_tokens=0,
                chunks_used=0,
                document_scope=None,
            )

        # 2. Check if scoped to a specific document
        doc_scope_name = None
        where_filter = None
        if request.document_id:
            scoped_doc = guidance_service.get_document(request.document_id)
            if scoped_doc:
                doc_scope_name = f"{scoped_doc.title} (v{scoped_doc.version})"
                # Filter by document_id in Chroma
                where_filter = {"document_id": request.document_id}

        # 3. Retrieve top-k chunks
        retrieved_chunks: List[RetrievalResult] = []
        try:
            if where_filter:
                # Retrieve with document filter
                try:
                    query_embeddings = None
                    from healthcompass.vector_store import embed_query
                    query_embeddings = embed_query(request.question)
                    results = collection.query(
                        query_embeddings=[query_embeddings],
                        n_results=min(request.top_k, max(collection.count(), 1)),
                        where=where_filter,
                        include=["documents", "metadatas", "distances"],
                    )
                    if results["ids"] and results["ids"][0]:
                        for i in range(len(results["ids"][0])):
                            retrieved_chunks.append(
                                RetrievalResult(
                                    chunk_id=results["ids"][0][i],
                                    source=results["metadatas"][0][i].get("source", ""),
                                    chunk_index=results["metadatas"][0][i].get("chunk_id", str(i)),
                                    distance=results["distances"][0][i] if results["distances"] else 0.0,
                                    text=results["documents"][0][i],
                                    metadata=results["metadatas"][0][i],
                                )
                            )
                except Exception:
                    # Fallback to general retrieval if where filter had no matches or unsupported
                    retrieved_chunks = retrieve(request.question, k=request.top_k, collection=collection)
            else:
                retrieved_chunks = retrieve(request.question, k=request.top_k, collection=collection)
        except Exception as e:
            error_msg = str(e)
            if "empty collection" in error_msg.lower():
                return AskResponse(
                    answer="No guidance documents are available in this collection.",
                    sources=[],
                    context_tokens=0,
                    chunks_used=0,
                )
            raise

        if not retrieved_chunks:
            return AskResponse(
                answer=(
                    "### No Relevant Guidance Found\n\n"
                    f"The current HealthCompass knowledge base does not contain enough relevant information to answer: *\"{request.question}\"*.\n\n"
                    "**Suggested Actions:**\n"
                    "- Try refining your clinical terms or question phrasing.\n"
                    "- Browse the **Guidance Library** to check available protocols.\n"
                    "- Upload the corresponding official guideline or circular."
                ),
                sources=[],
                context_tokens=0,
                chunks_used=0,
                document_scope=doc_scope_name,
            )

        # 4. Build context-injected prompt
        prompt_result = build_augmented_prompt(request.question, retrieved_chunks)

        # 5. Synthesize answer with Groq LLaMA 3.3 or fallback to grounded excerpts
        answer = ""
        try:
            chat_provider = get_chat_provider()
            answer = chat_provider.generate(
                prompt=prompt_result.prompt,
                temperature=0.1,
                max_tokens=1000,
            )
        except Exception as e:
            error_msg = str(e)
            # Synthesize direct grounded evidence answer from retrieved chunks
            excerpts_markdown = []
            for i, chunk in enumerate(retrieved_chunks[:3]):
                source_title = chunk.metadata.get("document_title") or chunk.source or "Official Protocol"
                page_str = f", Page {chunk.metadata.get('page_number')}" if chunk.metadata.get("page_number") else ""
                clean_text = chunk.text.strip().replace("\n", " ")
                if len(clean_text) > 300:
                    clean_text = clean_text[:300] + "..."
                excerpts_markdown.append(
                    f"**{i+1}. {source_title}{page_str}**\n> \"{clean_text}\""
                )

            answer = (
                f"### Evidence-Based Guidance Summary\n\n"
                f"Based on the approved clinical protocols retrieved for *\"{request.question}\"*:\n\n"
                + "\n\n".join(excerpts_markdown)
                + "\n\n---\n"
                + "> **System Note**: Generative answer synthesis requires `GROQ_API_KEY` configured in `.env`. The evidence citations above are extracted directly from your indexed guidance documents."
            )

        # 6. Map source grounding details
        chunk_map = {chunk.chunk_id: chunk for chunk in retrieved_chunks}
        sources: List[SourceInfo] = []
        for s in prompt_result.sources_used:
            chunk = chunk_map.get(s["chunk_id"])
            chunk_metadata = chunk.metadata if chunk else {}
            dist = s.get("distance", 0.0)
            rel_score = max(0.0, min(1.0, 1.0 - (dist / 2.0)))

            sources.append(
                SourceInfo(
                    chunk_id=s["chunk_id"],
                    source=s["source"],
                    chunk_index=str(s["chunk_index"]),
                    rank=s["rank"],
                    distance=dist,
                    excerpt=(chunk.text if chunk else "")[:450],
                    document_id=chunk_metadata.get("document_id"),
                    document_title=chunk_metadata.get("document_title") or s["source"],
                    page_number=chunk_metadata.get("page_number"),
                    authority=chunk_metadata.get("authority"),
                    version=chunk_metadata.get("version"),
                    relevance_score=round(rel_score, 2),
                )
            )

        return AskResponse(
            answer=answer,
            sources=sources,
            context_tokens=prompt_result.context_tokens,
            chunks_used=prompt_result.chunks_used,
            document_scope=doc_scope_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "OPENAI_API_KEY" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable: OpenAI API key not configured.",
            ) from e
        raise HTTPException(status_code=500, detail=str(e)) from e


# ─── Updates Endpoints (stub for frontend compatibility) ─────────


@app.get("/api/updates/unread/count")
def get_unread_count():
    """Return unread updates count. Stub endpoint for frontend AppShell compatibility."""
    return {"count": 0}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
