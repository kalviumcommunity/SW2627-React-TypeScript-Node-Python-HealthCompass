"""AI Client provider supporting free Google Gemini API and OpenAI API."""

import os
from typing import Optional, Tuple

from openai import OpenAI

# Gemini models (Free tier on Google AI Studio: https://aistudio.google.com/app/apikey)
DEFAULT_GEMINI_CHAT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_GEMINI_EMBEDDING_MODEL = "text-embedding-004"
GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# OpenAI models
DEFAULT_OPENAI_CHAT_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_BASE_URL = "https://api.openai.com/v1"


def is_gemini_active() -> bool:
    """Return True if GEMINI_API_KEY is configured in the environment."""
    return bool(os.getenv("GEMINI_API_KEY"))


def get_chat_client() -> Tuple[Optional[OpenAI], str]:
    """Get initialized chat completion client and active model name.

    Prefers GEMINI_API_KEY (free), falling back to OPENAI_API_KEY.
    Returns (client, model_name). If neither key is configured, returns (None, default_model).
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        base_url = os.getenv("GEMINI_BASE_URL", GEMINI_OPENAI_BASE_URL)
        model = os.getenv("CHAT_MODEL") or os.getenv("OPENAI_MODEL") or DEFAULT_GEMINI_CHAT_MODEL
        client = OpenAI(api_key=gemini_key, base_url=base_url)
        return client, model

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        base_url = os.getenv("OPENAI_BASE_URL", OPENAI_BASE_URL)
        model = os.getenv("CHAT_MODEL") or os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_CHAT_MODEL
        client = OpenAI(api_key=openai_key, base_url=base_url)
        return client, model

    # Offline / demonstration mode
    default_model = os.getenv("CHAT_MODEL") or DEFAULT_GEMINI_CHAT_MODEL
    return None, default_model


def get_embedding_client() -> Tuple[Optional[OpenAI], str, int]:
    """Get initialized embedding client, model name, and vector dimension.

    Prefers GEMINI_API_KEY (free), falling back to OPENAI_API_KEY.
    Returns (client, model_name, dimension).
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        base_url = os.getenv("GEMINI_BASE_URL", GEMINI_OPENAI_BASE_URL)
        model = os.getenv("EMBEDDING_MODEL", DEFAULT_GEMINI_EMBEDDING_MODEL)
        dimension = 768 if model == "text-embedding-004" else 1536
        client = OpenAI(api_key=gemini_key, base_url=base_url)
        return client, model, dimension

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        base_url = os.getenv("OPENAI_BASE_URL", OPENAI_BASE_URL)
        model = os.getenv("EMBEDDING_MODEL", DEFAULT_OPENAI_EMBEDDING_MODEL)
        dimension = 3072 if model == "text-embedding-3-large" else 1536
        client = OpenAI(api_key=openai_key, base_url=base_url)
        return client, model, dimension

    # Offline / demonstration mode
    return None, DEFAULT_GEMINI_EMBEDDING_MODEL, 768
