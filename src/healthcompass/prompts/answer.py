"""Prompt templates for grounded answers."""

ANSWER = (
    "You are a support assistant. Answer only from the supplied context.\n"
    "If the answer is not in the context, say you don't know.\n"
    "Cite the source document in your answer.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}"
)


def render(template: str, **values: str) -> str:
    """Fill a prompt template's named placeholders with runtime values."""
    return template.format(**values)
