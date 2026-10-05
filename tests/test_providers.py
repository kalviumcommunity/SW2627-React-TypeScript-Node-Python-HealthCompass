"""Tests for provider architecture."""

import os
import pytest
from unittest.mock import Mock, patch

from healthcompass.providers import (
    get_embedding_provider,
    get_chat_provider,
    LocalEmbeddingProvider,
    OpenAIEmbeddingProvider,
    GroqChatProvider,
)
from healthcompass.providers.chat import OpenAIChatProvider


class TestLocalEmbeddingProvider:
    """Tests for local embedding provider."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = LocalEmbeddingProvider(model_name="test-model")
        assert provider.model_name == "test-model"
        assert provider._model is None  # Lazy loading

    def test_get_model_name(self):
        """Test getting model name."""
        provider = LocalEmbeddingProvider(model_name="custom-model")
        assert provider.get_model_name() == "custom-model"


class TestOpenAIEmbeddingProvider:
    """Tests for OpenAI embedding provider."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = OpenAIEmbeddingProvider(
            api_key="test-key",
            model="text-embedding-3-small",
            base_url="https://api.openai.com/v1"
        )
        assert provider.api_key == "test-key"
        assert provider.model == "text-embedding-3-small"
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider._client is None  # Lazy loading

    def test_get_model_name(self):
        """Test getting model name."""
        provider = OpenAIEmbeddingProvider(api_key="test-key", model="custom-model")
        assert provider.get_model_name() == "custom-model"

    def test_get_dimension(self):
        """Test getting embedding dimension."""
        provider = OpenAIEmbeddingProvider(api_key="test-key", model="text-embedding-3-small")
        assert provider.get_dimension() == 1536

        provider = OpenAIEmbeddingProvider(api_key="test-key", model="text-embedding-3-large")
        assert provider.get_dimension() == 3072


class TestGroqChatProvider:
    """Tests for Groq chat provider."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = GroqChatProvider(
            api_key="test-key",
            model="llama-3.3-70b-versatile",
            base_url="https://api.groq.com/openai/v1"
        )
        assert provider.api_key == "test-key"
        assert provider.model == "llama-3.3-70b-versatile"
        assert provider.base_url == "https://api.groq.com/openai/v1"
        assert provider._client is None  # Lazy loading

    def test_get_model_name(self):
        """Test getting model name."""
        provider = GroqChatProvider(api_key="test-key", model="custom-model")
        assert provider.get_model_name() == "custom-model"


class TestOpenAIChatProvider:
    """Tests for OpenAI chat provider."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = OpenAIChatProvider(
            api_key="test-key",
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1"
        )
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4o-mini"
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider._client is None  # Lazy loading

    def test_get_model_name(self):
        """Test getting model name."""
        provider = OpenAIChatProvider(api_key="test-key", model="custom-model")
        assert provider.get_model_name() == "custom-model"


class TestProviderFactory:
    """Tests for provider factory functions."""

    def test_get_embedding_provider_local(self):
        """Test getting local embedding provider."""
        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "local"}):
            provider = get_embedding_provider()
            assert isinstance(provider, LocalEmbeddingProvider)

    def test_get_embedding_provider_openai(self):
        """Test getting OpenAI embedding provider."""
        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"}):
            provider = get_embedding_provider()
            assert isinstance(provider, OpenAIEmbeddingProvider)

    def test_get_embedding_provider_openai_missing_key(self):
        """Test OpenAI provider with missing API key."""
        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "openai"}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
                get_embedding_provider()

    def test_get_embedding_provider_invalid(self):
        """Test invalid embedding provider."""
        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "invalid"}):
            with pytest.raises(ValueError, match="Invalid EMBEDDING_PROVIDER"):
                get_embedding_provider()

    def test_get_chat_provider_groq(self):
        """Test getting Groq chat provider."""
        with patch.dict(os.environ, {"CHAT_PROVIDER": "groq", "GROQ_API_KEY": "test-key"}):
            provider = get_chat_provider()
            assert isinstance(provider, GroqChatProvider)

    def test_get_chat_provider_groq_missing_key(self):
        """Test Groq provider with missing API key."""
        with patch.dict(os.environ, {"CHAT_PROVIDER": "groq"}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY is required"):
                get_chat_provider()

    def test_get_chat_provider_openai(self):
        """Test getting OpenAI chat provider."""
        with patch.dict(os.environ, {"CHAT_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"}):
            provider = get_chat_provider()
            assert isinstance(provider, OpenAIChatProvider)

    def test_get_chat_provider_openai_missing_key(self):
        """Test OpenAI provider with missing API key."""
        with patch.dict(os.environ, {"CHAT_PROVIDER": "openai"}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
                get_chat_provider()

    def test_get_chat_provider_invalid(self):
        """Test invalid chat provider."""
        with patch.dict(os.environ, {"CHAT_PROVIDER": "invalid"}):
            with pytest.raises(ValueError, match="Invalid CHAT_PROVIDER"):
                get_chat_provider()

    def test_get_embedding_provider_default(self):
        """Test default embedding provider is local."""
        with patch.dict(os.environ, {}, clear=True):
            provider = get_embedding_provider()
            assert isinstance(provider, LocalEmbeddingProvider)

    def test_get_chat_provider_default(self):
        """Test default chat provider is Groq."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY is required"):
                get_chat_provider()
