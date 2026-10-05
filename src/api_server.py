"""FastAPI server for HealthCompass RAG application."""

from typing import List, Optional

# Ensure src/ is on sys.path for direct module imports
src_dir = str(Path(__file__).resolve().parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from healthcompass.providers import get_chat_provider, get_embedding_provider
from healthcompass.rag import build_augmented_prompt
from healthcompass.vector_store import initialize_vector_store, retrieve

load_dotenv()

app = FastAPI(title="HealthCompass API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    """Request model for ask endpoint."""

    question: str


class SourceInfo(BaseModel):
    """Source information from retrieval."""

    chunk_id: str
    source: str
    chunk_index: str
    rank: int
    distance: float
    excerpt: str = ""


class AskResponse(BaseModel):
    """Response model for ask endpoint."""

    answer: str
    sources: List[SourceInfo]
    context_tokens: int
    chunks_used: int


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


# Sample/demo data for pages that don't have backend data yet
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


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "HealthCompass API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """Health check endpoint with provider information."""
    try:
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "local")
        chat_provider = os.getenv("CHAT_PROVIDER", "groq")
        embedding_model = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        if embedding_provider == "openai":
            embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        chat_model = os.getenv("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")
        if chat_provider == "openai":
            chat_model = os.getenv("CHAT_MODEL", "gpt-4o-mini")

        return {
            "status": "healthy",
            "chat_provider": chat_provider,
            "embedding_provider": embedding_provider,
            "chat_model": chat_model,
            "embedding_model": embedding_model,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/ask", response_model=AskResponse)
def ask_healthcompass(request: AskRequest):
    """
    Ask HealthCompass a question using RAG pipeline.

    This endpoint:
    1. Embeds the user query using configured provider
    2. Retrieves relevant chunks from vector database
    3. Builds augmented prompt with context
    4. Generates answer using configured chat provider
    5. Returns answer with sources
    """
    try:
        # Initialize vector database
        collection = initialize_vector_store()

        # If provider-specific collection is empty, check if base collection has indexed documents
        if collection.count() == 0:
            try:
                import chromadb
                db_path = os.getenv("CHROMA_DB_PATH", "data/chroma_db")
                base_name = os.getenv("CHROMA_COLLECTION_NAME", "healthcompass_documents")
                fallback_client = chromadb.PersistentClient(path=db_path)
                fallback_col = fallback_client.get_collection(name=base_name)
                if fallback_col.count() > 0:
                    collection = fallback_col
            except Exception:
                pass

        if collection.count() == 0:
            return AskResponse(
                answer="No documents are currently indexed in the knowledge base. Please run the ingestion pipeline to index public-health guidelines and directives.",
                sources=[],
                context_tokens=0,
                chunks_used=0,
            )

        # Try to retrieve relevant chunks
        try:
            retrieved_chunks = retrieve(request.question, k=5, collection=collection)
        except Exception as e:
            error_msg = str(e)
            if "empty collection" in error_msg.lower():
                return AskResponse(
                    answer="No documents found in the current collection. Please run ingestion to index guidance documents.",
                    sources=[],
                    context_tokens=0,
                    chunks_used=0,
                )
            raise

        if not retrieved_chunks:
            return AskResponse(
                answer="I don't have enough information in the provided context to answer this question.",
                sources=[],
                context_tokens=0,
                chunks_used=0,
            )

        # Build augmented prompt
        prompt_result = build_augmented_prompt(request.question, retrieved_chunks)

        # Generate answer using chat provider
        try:
            chat_provider = get_chat_provider()
            answer = chat_provider.generate(
                prompt=prompt_result.prompt,
                temperature=0.1,
                max_tokens=1000,
            )
        except Exception as e:
            error_msg = str(e)
            # Synthesize direct evidence answer from retrieved chunks if LLM key is unconfigured
            excerpts_text = "\n\n".join([f"**Excerpt {i+1}**:\n> {chunk.text.strip()[:350]}..." for i, chunk in enumerate(retrieved_chunks[:2])])
            answer = (
                f"### Evidence-Based Guidance Summary\n\n"
                f"Based on the official retrieved guidelines for *\"{request.question}\"*:\n\n"
                f"{excerpts_text}\n\n"
                f"> **Notice**: Configure `GROQ_API_KEY` or `OPENAI_API_KEY` in your `.env` file to enable full LLaMA 3.3 conversational synthesis."
            )

        # Build a map of chunk_id -> text from retrieved chunks
        chunk_text_map = {chunk.chunk_id: chunk.text for chunk in retrieved_chunks}

        # Convert sources to response format
        sources = [
            SourceInfo(
                chunk_id=source_info["chunk_id"],
                source=source_info["source"],
                chunk_index=source_info["chunk_index"],
                rank=source_info["rank"],
                distance=source_info["distance"],
                excerpt=chunk_text_map.get(source_info["chunk_id"], "")[:500],
            )
            for source_info in prompt_result.sources_used
        ]

        return AskResponse(
            answer=answer,
            sources=sources,
            context_tokens=prompt_result.context_tokens,
            chunks_used=prompt_result.chunks_used,
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "OPENAI_API_KEY" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable: OpenAI API key not configured. Please contact your administrator.",
            ) from e
        raise HTTPException(status_code=500, detail=str(e)) from e


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
    """Get dashboard statistics with contextual subtitles."""
    critical_count = sum(1 for a in SAMPLE_ALERTS if a.severity == "Critical")
    return {
        "active_alerts": len(SAMPLE_ALERTS),
        "active_alerts_subtitle": f"{critical_count} critical" if critical_count else "All stable",
        "new_guidance": len(SAMPLE_GUIDANCE),
        "new_guidance_subtitle": f"{len(SAMPLE_GUIDANCE)} added this week",
        "policy_updates": len(SAMPLE_UPDATES),
        "policy_updates_subtitle": "Latest v4.2",
        "saved_guidance": 8,
        "saved_guidance_subtitle": "Frequently used",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
