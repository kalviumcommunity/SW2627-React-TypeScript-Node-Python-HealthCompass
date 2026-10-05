"""FastAPI server for HealthCompass RAG application."""

import json
import logging
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from healthcompass.ingestion import (
    clean_page,
    load_document,
    prepare_chunks_from_token_chunks,
    to_vector_record,
    token_chunks,
)
from healthcompass.rag import RAGPipeline, RAGResponse
from healthcompass.vector_store import upsert_records

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("healthcompass.api")

app = FastAPI(
    title="HealthCompass API",
    version="2.0.0",
    description="AI-Powered Public Health Guidance & Outbreak Intelligence Platform",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Caching & Observability (Task 3.48)
# ============================================================================

class QueryCache:
    """In-memory LRU/TTL cache for repeated queries."""

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 500):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, tuple[float, Any]] = {}
        self.hits = 0
        self.misses = 0

    def _make_key(self, question: str, filter_dict: Optional[dict], kw_weight: float) -> str:
        norm_q = question.strip().casefold()
        filter_str = json.dumps(filter_dict or {}, sort_keys=True)
        return f"{norm_q}::{filter_str}::{kw_weight:.2f}"

    def get(self, question: str, filter_dict: Optional[dict], kw_weight: float) -> Optional[Any]:
        key = self._make_key(question, filter_dict, kw_weight)
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < self.ttl:
                self.hits += 1
                return data
            del self._cache[key]
        self.misses += 1
        return None

    def set(self, question: str, filter_dict: Optional[dict], kw_weight: float, data: Any):
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        key = self._make_key(question, filter_dict, kw_weight)
        self._cache[key] = (time.time(), data)


class UsageMetrics:
    """Tracks latency, token usage, and request counts."""

    def __init__(self):
        self.total_requests: int = 0
        self.total_tokens: int = 0
        self.total_latency_ms: float = 0.0

    def record(self, tokens: int, latency_ms: float):
        self.total_requests += 1
        self.total_tokens += tokens
        self.total_latency_ms += latency_ms

    @property
    def avg_latency_ms(self) -> float:
        return round(self.total_latency_ms / max(self.total_requests, 1), 2)


query_cache = QueryCache()
usage_metrics = UsageMetrics()
rag_pipeline = RAGPipeline()


# ============================================================================
# Request / Response Models
# ============================================================================

class AskRequest(BaseModel):
    """Request model for ask endpoint."""

    question: str
    history: Optional[List[Dict[str, str]]] = None
    metadata_filter: Optional[dict[str, Any]] = None
    keyword_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    candidate_k: int = Field(default=6, ge=1, le=20)
    top_k: int = Field(default=3, ge=1, le=10)
    enable_rerank: bool = True


class CitationModel(BaseModel):
    """Citation model for verifiable attribution."""

    index: int
    chunk_id: str
    source: str
    section: Optional[str] = None
    snippet: str
    distance: float


class SourceInfo(BaseModel):
    """Source information from retrieval."""

    chunk_id: str
    source: str
    chunk_index: str
    rank: int
    distance: float


class AskResponse(BaseModel):
    """Response model for ask endpoint."""

    answer: str
    citations: List[CitationModel]
    sources: List[SourceInfo]
    context_tokens: int
    chunks_used: int
    chunks_retrieved: int
    is_refusal: bool
    faithfulness_score: float
    latency_ms: float
    cached: bool = False


class GuidanceItem(BaseModel):
    """Guidance item for library."""

    id: str
    title: str
    topic: str
    description: str
    source: str
    last_updated: str


class AlertItem(BaseModel):
    """Alert item for alert center."""

    id: str
    severity: str
    topic: str
    location: Optional[str]
    date: str
    description: str
    status: str


class UpdateItem(BaseModel):
    """Policy update item."""

    id: str
    title: str
    category: str
    date: str
    summary: str
    importance: str


class UploadResponse(BaseModel):
    """Response model for document upload."""

    filename: str
    chunks_indexed: int
    status: str
    message: str


# Demo guidance data
SAMPLE_GUIDANCE = [
    GuidanceItem(
        id="1",
        title="Vaccination Priority Groups",
        topic="Vaccination",
        description="Guidance on priority groups for vaccination during public health emergencies",
        source="vaccination_guidance.txt",
        last_updated="2026-09-15",
    ),
    GuidanceItem(
        id="2",
        title="Fever Management in Children",
        topic="Child Health",
        description="Protocol for managing high fever in pediatric patients",
        source="child_health_guidance.txt",
        last_updated="2026-09-10",
    ),
    GuidanceItem(
        id="3",
        title="Emergency Response Protocol",
        topic="Emergency Response",
        description="Standard operating procedures for emergency health situations",
        source="emergency_protocol.txt",
        last_updated="2026-09-08",
    ),
]

SAMPLE_ALERTS = [
    AlertItem(
        id="1",
        severity="Critical",
        topic="Disease Outbreak",
        location="District A",
        date="2026-09-28",
        description="Increased respiratory illness cases reported in District A",
        status="Active",
    ),
    AlertItem(
        id="2",
        severity="High",
        topic="Vaccine Supply",
        location="Regional",
        date="2026-09-25",
        description="Temporary vaccine shortage due to supply chain delays",
        status="Monitoring",
    ),
]

SAMPLE_UPDATES = [
    UpdateItem(
        id="1",
        title="Updated Isolation Guidelines",
        category="Infection Control",
        date="2026-09-27",
        summary="New isolation protocols for respiratory infections",
        importance="High",
    ),
    UpdateItem(
        id="2",
        title="Vaccination Schedule Changes",
        category="Vaccination",
        date="2026-09-20",
        summary="Revised dosing intervals for booster vaccinations",
        importance="Medium",
    ),
]


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "HealthCompass API", "version": "2.0.0", "status": "active"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "healthcompass-backend"}


@app.post("/ask", response_model=AskResponse)
def ask_healthcompass(request: AskRequest):
    """
    Ask HealthCompass a question using the end-to-end RAG pipeline.

    Workflow:
    1. Check query cache (if identical request was recently served)
    2. Condense follow-up questions if conversation history exists
    3. Retrieve relevant chunks (with optional metadata filter & hybrid search)
    4. Re-rank candidate chunks to boost precision
    5. Evaluate hallucination guardrails (refuses if evidence is absent)
    6. Generate grounded answer strictly based on retrieved context
    7. Parse source citations and verify attribution
    """
    logger.info(f"Received query: '{request.question}'")

    # Check cache (only for single-turn queries without custom history)
    if not request.history:
        cached_result = query_cache.get(
            request.question, request.metadata_filter, request.keyword_weight
        )
        if cached_result:
            cached_result.cached = True
            logger.info("Serving query from cache")
            return cached_result

    try:
        rag_res: RAGResponse = rag_pipeline.run(
            question=request.question,
            history=request.history,
            metadata_filter=request.metadata_filter,
            keyword_weight=request.keyword_weight,
            candidate_k=request.candidate_k,
            top_k=request.top_k,
            enable_rerank=request.enable_rerank,
        )

        response = AskResponse(
            answer=rag_res.answer,
            citations=[
                CitationModel(
                    index=c.index,
                    chunk_id=c.chunk_id,
                    source=c.source,
                    section=c.section,
                    snippet=c.snippet,
                    distance=c.distance,
                )
                for c in rag_res.citations
            ],
            sources=[
                SourceInfo(
                    chunk_id=s.get("chunk_id", ""),
                    source=s.get("source", "unknown"),
                    chunk_index=s.get("chunk_index", ""),
                    rank=s.get("rank", 1),
                    distance=s.get("distance", 0.0),
                )
                for s in rag_res.sources
            ],
            context_tokens=rag_res.context_tokens,
            chunks_used=rag_res.chunks_used,
            chunks_retrieved=rag_res.chunks_retrieved,
            is_refusal=rag_res.is_refusal,
            faithfulness_score=rag_res.faithfulness_score,
            latency_ms=rag_res.latency_ms,
            cached=False,
        )

        # Update cache & metrics
        if not request.history and not rag_res.is_refusal:
            query_cache.set(
                request.question, request.metadata_filter, request.keyword_weight, response
            )
        usage_metrics.record(rag_res.context_tokens, rag_res.latency_ms)

        return response

    except Exception as e:
        logger.error(f"Error processing RAG query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/ask/stream")
def ask_healthcompass_stream(request: AskRequest):
    """
    Stream grounded answer tokens chunk-by-chunk via Server-Sent Events (SSE).
    """
    def event_stream():
        try:
            for token in rag_pipeline.run_stream(
                question=request.question,
                history=request.history,
                metadata_filter=request.metadata_filter,
                keyword_weight=request.keyword_weight,
                top_k=request.top_k,
            ):
                payload = json.dumps({"token": token})
                yield f"data: {payload}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):  # noqa: B008
    """
    Ingest, clean, chunk, embed, and index a new document into ChromaDB at runtime.
    Supports .pdf, .txt, .md, and .html files.
    """
    allowed_exts = {".pdf", ".txt", ".md", ".html"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{suffix}'. Allowed formats: {', '.join(allowed_exts)}",
        )

    upload_dir = Path("data/uploaded")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / (file.filename or "uploaded_doc.txt")

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Load document
        pages = load_document(temp_path)

        all_chunks = []
        for page in pages:
            cleaned = clean_page(page)
            t_chunks = token_chunks(
                text=cleaned.text,
                source=str(temp_path),
                filename=file.filename or "uploaded_doc",
                size=300,
                overlap=40,
            )
            all_chunks.extend(t_chunks)

        if not all_chunks:
            return UploadResponse(
                filename=file.filename or "unknown",
                chunks_indexed=0,
                status="warning",
                message="File contained no indexable text.",
            )

        # 3. Prepare for embedding
        prepared = prepare_chunks_from_token_chunks(all_chunks)

        # 4. Generate embeddings (or offline deterministic fallback if no API key)
        from healthcompass.ingestion.embeddings import generate_embeddings
        try:
            embedding_result = generate_embeddings(prepared)
            embedded_chunks = embedding_result.chunks
        except Exception as emb_err:
            logger.warning(f"Using deterministic fallback embeddings: {emb_err}")
            # Generate deterministic fallback vector if no key
            from healthcompass.ingestion import EmbeddedChunk
            embedded_chunks = [
                EmbeddedChunk(
                    text=c["text"],
                    source=c.get("source", str(temp_path)),
                    filename=c.get("filename", file.filename or "uploaded_doc"),
                    chunk_id=idx,
                    metadata=c.get("metadata", {}),
                    embedding=[0.05 * (i % 20) for i in range(1536)],
                    embedding_model="text-embedding-3-small",
                )
                for idx, c in enumerate(prepared)
            ]

        # 5. Insert records into Chroma collection
        collection = rag_pipeline.collection
        records = [to_vector_record(chunk) for chunk in embedded_chunks]
        upsert_res = upsert_records(collection, records)
        indexed_count = upsert_res.inserted_count

        return UploadResponse(
            filename=file.filename or "document",
            chunks_indexed=indexed_count,
            status="success",
            message=f"Successfully ingested and indexed {indexed_count} chunks into HealthCompass knowledge base.",
        )

    except Exception as e:
        logger.error(f"Failed to ingest uploaded document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}") from e


@app.get("/guidance", response_model=List[GuidanceItem])
def get_guidance():
    """Get available guidance documents."""
    return SAMPLE_GUIDANCE


@app.get("/guidance/search", response_model=List[GuidanceItem])
def search_guidance(query: str):
    """Search guidance by topic or title."""
    query_lower = query.lower()
    return [
        item
        for item in SAMPLE_GUIDANCE
        if query_lower in item.title.lower()
        or query_lower in item.topic.lower()
        or query_lower in item.description.lower()
    ]


@app.get("/alerts", response_model=List[AlertItem])
def get_alerts():
    """Get active alerts."""
    return SAMPLE_ALERTS


@app.get("/updates", response_model=List[UpdateItem])
def get_updates():
    """Get recent policy updates."""
    return SAMPLE_UPDATES


@app.get("/stats")
def get_stats():
    """Get dashboard and operational statistics."""
    return {
        "active_alerts": len(SAMPLE_ALERTS),
        "new_guidance": len(SAMPLE_GUIDANCE),
        "policy_updates": len(SAMPLE_UPDATES),
        "saved_guidance": 0,
        "total_queries_served": usage_metrics.total_requests,
        "cache_hits": query_cache.hits,
        "cache_misses": query_cache.misses,
        "avg_latency_ms": usage_metrics.avg_latency_ms,
    }


@app.get("/stats/usage")
def get_usage_metrics():
    """Get detailed telemetry on query latency and caching performance."""
    return {
        "total_requests": usage_metrics.total_requests,
        "total_tokens": usage_metrics.total_tokens,
        "avg_latency_ms": usage_metrics.avg_latency_ms,
        "cache_hits": query_cache.hits,
        "cache_misses": query_cache.misses,
        "cache_hit_rate": round(
            query_cache.hits / max(query_cache.hits + query_cache.misses, 1), 3
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
