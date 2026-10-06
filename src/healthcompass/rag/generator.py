"""Grounded answer generation module for HealthCompass RAG system."""

from typing import Any, Iterator, Optional

GROUNDED_SYSTEM_INSTRUCTION = (
    "You are HealthCompass, an AI assistant providing official public health guidance.\n"
    "CRITICAL RULES:\n"
    "1. Answer ONLY using the provided Context documents.\n"
    "2. If the Context does not provide the specific answer, you MUST state: "
    "'I do not have enough verified information in the official guidance to answer this question.'\n"
    "3. Never guess, assume, or extrapolate beyond what is explicitly written.\n"
    "4. Always cite your sources inline using bracket notation, e.g. [1], [2], corresponding to the source numbers."
)


def _offline_grounded_fallback(prompt: str) -> str:
    """Deterministic offline fallback for environments without an active OpenAI API key."""
    # Check if context is empty or question asks for missing info
    lines = prompt.splitlines()
    context_lines = []
    question = ""
    is_context = False

    for line in lines:
        if line.startswith("Context:"):
            is_context = True
            continue
        elif line.startswith("Question:"):
            is_context = False
            question = line.replace("Question:", "").strip()
            continue

        if is_context and line.strip():
            context_lines.append(line.strip())

    if not context_lines:
        return "I do not have enough verified information in the official guidance to answer this question."

    # Look for relevant context statements
    content_text = " ".join([line for line in context_lines if not line.startswith("[")])
    sentences = [s.strip() for s in content_text.split(".") if s.strip()]

    q_terms = [t.lower() for t in question.split() if len(t) > 3]
    matching = [
        s for s in sentences
        if any(term in s.lower() for term in q_terms)
    ]

    if matching:
        return f"{matching[0]}. [1]"
    elif sentences:
        return f"{sentences[0]}. [1]"

    return "I do not have enough verified information in the official guidance to answer this question."


def generate_grounded_answer(
    prompt: str,
    client: Optional[Any] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 500,
) -> str:
    """Generate a grounded answer using the provided augmented prompt.

    Args:
        prompt: Complete prompt including system instructions, context, and question.
        client: Optional OpenAI/Gemini client instance.
        model: Model name to use (defaults to Gemini or OpenAI model).
        temperature: Sampling temperature (0.0 recommended for factual grounding).
        max_tokens: Maximum tokens in generated completion.

    Returns:
        Generated answer string.
    """
    from healthcompass.ai_client import get_chat_client

    active_client = client
    model_name = model

    if active_client is None:
        active_client, default_model = get_chat_client()
        if not model_name:
            model_name = default_model

    if active_client is not None:
        try:
            response = active_client.chat.completions.create(
                model=model_name or "gemini-3.5-flash-lite",
                messages=[
                    {"role": "system", "content": GROUNDED_SYSTEM_INSTRUCTION},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            # If API fails or key is invalid/expired, fall back gracefully
            pass

    return _offline_grounded_fallback(prompt)


def generate_grounded_answer_stream(
    prompt: str,
    client: Optional[Any] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 500,
) -> Iterator[str]:
    """Stream grounded answer tokens chunk-by-chunk.

    Args:
        prompt: Complete prompt including system instructions, context, and question.
        client: Optional OpenAI/Gemini client instance.
        model: Model name to use.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate.

    Yields:
        Individual string tokens as they arrive.
    """
    from healthcompass.ai_client import get_chat_client

    active_client = client
    model_name = model

    if active_client is None:
        active_client, default_model = get_chat_client()
        if not model_name:
            model_name = default_model

    if active_client is not None:
        try:
            stream = active_client.chat.completions.create(
                model=model_name or "gemini-3.5-flash-lite",
                messages=[
                    {"role": "system", "content": GROUNDED_SYSTEM_INSTRUCTION},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            return
        except Exception:
            pass

    # Offline streaming fallback
    full_answer = _offline_grounded_fallback(prompt)
    words = full_answer.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
