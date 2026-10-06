"""Embedding provider abstraction for HealthCompass RAG system."""

import os
from abc import ABC, abstractmethod
from typing import List

from dotenv import load_dotenv

load_dotenv()


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of documents.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the embedding model being used.

        Returns:
            Model name string
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of the embedding vectors.

        Returns:
            Vector dimension
        """
        pass


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize local embedding provider.

        Args:
            model_name: Name of the sentence-transformers model
        """
        self.model_name = model_name
        self._model = None
        self._dimension = None

    def _load_model(self):
        """Lazy-load the model on first use."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "sentence-transformers is not installed. "
                    "Install it with: pip install sentence-transformers"
                )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for documents using local model.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        self._load_model()
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return [[float(x) for x in emb] for emb in embeddings]

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a query using local model.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        self._load_model()
        embedding = self._model.encode(text, convert_to_numpy=True)
        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return [float(x) for x in embedding]

    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model_name

    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        self._load_model()
        return self._dimension


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small", base_url: str = "https://api.openai.com/v1"):
        """Initialize OpenAI embedding provider.

        Args:
            api_key: OpenAI API key
            model: Embedding model name
            base_url: API base URL
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client = None
        self._dimension = None

        # Known dimensions for OpenAI models
        self._dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }

    def _load_client(self):
        """Lazy-load the OpenAI client on first use."""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                raise ImportError(
                    "openai is not installed. Install it with: pip install openai"
                )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for documents using OpenAI.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors as plain Python lists of floats
        """
        self._load_client()
        response = self._client.embeddings.create(input=texts, model=self.model)
        # Ensure each embedding is a plain list of floats
        return [
            [float(v) for v in embedding.embedding]
            for embedding in response.data
        ]

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a query using OpenAI.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector as plain Python list of floats
        """
        self._load_client()
        response = self._client.embeddings.create(input=[text], model=self.model)
        return [float(v) for v in response.data[0].embedding]

    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model

    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        return self._dimensions.get(self.model, 1536)


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Google Gemini embedding provider using OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-004",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/",
    ):
        """Initialize Gemini embedding provider.

        Args:
            api_key: Gemini API key
            model: Embedding model name (default: text-embedding-004)
            base_url: Google OpenAI-compatible endpoint
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client = None

    def _load_client(self):
        """Lazy-load the OpenAI client on first use."""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                raise ImportError(
                    "openai is not installed. Install it with: pip install openai"
                )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of documents."""
        self._load_client()
        response = self._client.embeddings.create(input=texts, model=self.model)
        return [[float(v) for v in item.embedding] for item in response.data]

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        self._load_client()
        response = self._client.embeddings.create(input=[text], model=self.model)
        return [float(v) for v in response.data[0].embedding]

    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model

    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        return 768


def get_embedding_provider() -> EmbeddingProvider:
    """Get the configured embedding provider based on environment variables.

    Returns:
        EmbeddingProvider instance

    Raises:
        ValueError: If configuration is invalid
    """
    provider = os.getenv("EMBEDDING_PROVIDER")
    if not provider:
        provider = "local"
    else:
        provider = provider.lower()

    if provider == "local":
        model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        return LocalEmbeddingProvider(model_name=model_name)

    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini"
            )
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
        base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
        return GeminiEmbeddingProvider(api_key=api_key, model=model, base_url=base_url)

    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai"
            )
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return OpenAIEmbeddingProvider(api_key=api_key, model=model, base_url=base_url)

    else:
        raise ValueError(
            f"Invalid EMBEDDING_PROVIDER: {provider}. "
            "Must be 'local', 'gemini', or 'openai'."
        )
