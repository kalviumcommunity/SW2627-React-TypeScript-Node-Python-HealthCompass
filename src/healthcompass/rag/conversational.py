"""Conversational RAG and query condensation for multi-turn dialogues."""

import re
from typing import Any, Dict, List, Optional

CONDENSE_PROMPT_TEMPLATE = (
    "Given the conversation history and a follow-up question, rephrase the follow-up question "
    "into a standalone search query that contains all context needed for document retrieval.\n"
    "Do NOT answer the question. Only output the rephrased standalone search query.\n\n"
    "Chat History:\n{history}\n\n"
    "Follow-up Question: {question}\n\n"
    "Standalone Query:"
)


def _format_history_text(history: List[Dict[str, str]], max_turns: int = 4) -> str:
    """Format recent chat history into plain text."""
    recent = history[-max_turns:]
    lines = []
    for msg in recent:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "").strip()
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _fallback_condensation(query: str, history: List[Dict[str, str]]) -> str:
    """Heuristic fallback to enrich query with key terms from previous user turns if LLM unavailable."""
    if not history:
        return query

    # Find last user query
    last_user_query = ""
    for msg in reversed(history):
        if msg.get("role") == "user":
            last_user_query = msg.get("content", "")
            break

    if not last_user_query:
        return query

    # Check if query is short / anaphoric (e.g. "what about children?", "how about vaccinated?")
    is_followup = any(
        query.lower().startswith(prefix)
        for prefix in ["what about", "how about", "and for", "what if", "does it apply", "why"]
    ) or len(query.split()) <= 4

    if is_followup:
        # Extract potential topics/districts (capitalized words or medical terms) from last query
        stopwords = {"what", "is", "the", "in", "for", "a", "an", "at", "to", "of", "and", "or"}
        # Match "District <name>" or health domain terms or non-stopwords with len >= 4
        district_match = re.findall(r"\bDistrict\s+[A-Za-z0-9]+\b", last_user_query, re.IGNORECASE)
        keywords = re.findall(r"\b(?:fever|isolation|quarantine|vaccin\w+|pediatric|outbreak|protocol)\b", last_user_query, re.IGNORECASE)
        
        candidates = district_match + keywords
        if not candidates:
            words = [w for w in re.findall(r"\b[A-Za-z0-9_-]+\b", last_user_query) if w.lower() not in stopwords and len(w) >= 4]
            candidates = words

        unique_entities = []
        for e in candidates:
            if e.lower() not in query.lower() and e.lower() not in [x.lower() for x in unique_entities]:
                unique_entities.append(e)

        if unique_entities:
            return f"{query} regarding {' '.join(unique_entities[:2])}"

    return query


def condense_followup_question(
    query: str,
    history: Optional[List[Dict[str, str]]] = None,
    client: Optional[Any] = None,
    model: str = "gpt-4o-mini",
) -> str:
    """Condense a follow-up question using conversation history into a standalone query.

    Args:
        query: Follow-up question from user.
        history: Prior conversation turns as list of {'role': ..., 'content': ...}.
        client: Optional OpenAI client instance.
        model: Model name for condensation.

    Returns:
        Standalone search query with necessary context preserved.
    """
    if not history:
        return query.strip()

    history_text = _format_history_text(history)
    if not history_text:
        return query.strip()

    from healthcompass.ai_client import get_chat_client

    active_client = client
    model_name = model
    if active_client is None:
        active_client, default_model = get_chat_client()
        if not model_name:
            model_name = default_model

    if active_client is not None:
        try:
            prompt = CONDENSE_PROMPT_TEMPLATE.format(history=history_text, question=query)
            response = active_client.chat.completions.create(
                model=model_name or "gemini-3.5-flash-lite",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=60,
            )
            condensed = response.choices[0].message.content.strip()
            # If model returned quotes or prefix, clean it up
            condensed = re.sub(r'^(Standalone Query:\s*|["\'])', "", condensed)
            condensed = re.sub(r'["\']$', "", condensed).strip()
            if condensed:
                return condensed
        except Exception:
            # Fall back to heuristic condensation if API call fails
            pass

    return _fallback_condensation(query, history)
