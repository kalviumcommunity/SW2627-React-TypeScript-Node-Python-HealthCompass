"""Vector store for HealthCompass RAG system."""

from .chroma_store import (
    RetrievalResult,
    VectorRecord,
    VectorStoreConfig,
    VectorStoreError,
    embed_query,
    get_collection_info,
    get_record,
    get_vector_store_config,
    health_check,
    initialize_vector_store,
    insert_record,
    retrieve,
)

__all__ = [
    "RetrievalResult",
    "VectorRecord",
    "VectorStoreConfig",
    "VectorStoreError",
    "embed_query",
    "get_collection_info",
    "get_record",
    "get_vector_store_config",
    "health_check",
    "initialize_vector_store",
    "insert_record",
    "retrieve",
]
