"""Chat provider abstraction for HealthCompass RAG system."""

import os
from abc import ABC, abstractmethod
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class ChatProvider(ABC):
    """Abstract base class for chat providers."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response to a prompt.

        Args:
            prompt: The prompt to send to the chat model
            **kwargs: Additional model-specific parameters

        Returns:
            Generated response text
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the chat model being used.

        Returns:
            Model name string
        """
        pass


class GroqChatProvider(ChatProvider):
    """Groq chat provider using OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        base_url: str = "https://api.groq.com/openai/v1",
    ):
        """Initialize Groq chat provider.

        Args:
            api_key: Groq API key
            model: Chat model name (Groq uses Llama models)
            base_url: API base URL
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

    def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate a response using Groq.

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Generated response text
        """
        self._load_client()

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        return response.choices[0].message.content

    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model


class OpenAIChatProvider(ChatProvider):
    """OpenAI chat provider (optional/future)."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
    ):
        """Initialize OpenAI chat provider.

        Args:
            api_key: OpenAI API key
            model: Chat model name
            base_url: API base URL
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

    def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate a response using OpenAI.

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Generated response text
        """
        self._load_client()

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        return response.choices[0].message.content

    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model


class GeminiChatProvider(ChatProvider):
    """Google Gemini chat provider using OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.5-flash-lite",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/",
    ):
        """Initialize Gemini chat provider.

        Args:
            api_key: Gemini API key (Google AI Studio)
            model: Chat model name (default: gemini-3.5-flash-lite)
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

    def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate a response using Gemini."""
        self._load_client()

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        return response.choices[0].message.content

    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model


def get_chat_provider() -> ChatProvider:
    """Get the configured chat provider based on environment variables.

    Returns:
        ChatProvider instance

    Raises:
        ValueError: If configuration is invalid
    """
    provider = os.getenv("CHAT_PROVIDER")
    if not provider:
        if os.getenv("GEMINI_API_KEY"):
            provider = "gemini"
        elif os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY"):
            provider = "openai"
        else:
            provider = "groq"
    else:
        provider = provider.lower()

    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when CHAT_PROVIDER=gemini"
            )
        model = os.getenv("CHAT_MODEL") or os.getenv("GEMINI_CHAT_MODEL", "gemini-3.5-flash-lite")
        base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
        return GeminiChatProvider(api_key=api_key, model=model, base_url=base_url)

    elif provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is required when CHAT_PROVIDER=groq"
            )
        model = os.getenv("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")
        base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        return GroqChatProvider(api_key=api_key, model=model, base_url=base_url)

    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when CHAT_PROVIDER=openai"
            )
        model = os.getenv("CHAT_MODEL", "gpt-4o-mini")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return OpenAIChatProvider(api_key=api_key, model=model, base_url=base_url)

    else:
        raise ValueError(
            f"Invalid CHAT_PROVIDER: {provider}. "
            "Must be 'gemini', 'groq', or 'openai'."
        )
