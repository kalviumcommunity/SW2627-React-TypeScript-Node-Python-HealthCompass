import os
import re
import argparse
from collections.abc import MutableSequence

from dotenv import load_dotenv
from openai import OpenAI


REQUIRED_ENV = {
    "OPENAI_BASE_URL": "OpenAI base URL",
    "OPENAI_API_KEY": "OpenAI API key",
    "CHAT_MODEL": "Chat model",
    "EMBED_MODEL": "Embedding model",
}

SYSTEM_PROMPT = (
    "You are a support assistant for an internal docs tool. "
    "Answer in two sentences maximum. If you are unsure, say you don't know."
)
DEFAULT_CONTEXT_BUDGET = 6000
TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def build_messages(user_prompt: str, system_prompt: str = SYSTEM_PROMPT) -> list[dict[str, str]]:
    """Build a chat request with explicit system and user roles."""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def count_tokens(text: str) -> int:
    """Estimate tokens without requiring a model-specific tokenizer."""
    return len(TOKEN_PATTERN.findall(text))


def total_tokens(messages: list[dict[str, str]]) -> int:
    """Return the estimated token count for message content."""
    return sum(count_tokens(message.get("content", "")) for message in messages)


def trim(messages: MutableSequence[dict[str, str]], budget: int = DEFAULT_CONTEXT_BUDGET) -> None:
    """Drop the oldest non-system messages until the history fits the budget."""
    if budget < 1:
        raise ValueError("budget must be greater than zero")

    while total_tokens(list(messages)) > budget and len(messages) > 2:
        del messages[1]


class ConversationHistory:
    """Track a chat history and keep it below the configured context budget."""

    def __init__(
        self,
        system_prompt: str = SYSTEM_PROMPT,
        budget: int = DEFAULT_CONTEXT_BUDGET,
    ) -> None:
        self.budget = budget
        self.messages = [{"role": "system", "content": system_prompt}]

    def add_user_message(self, prompt: str) -> None:
        self.messages.append({"role": "user", "content": prompt})
        trim(self.messages, self.budget)

    def add_assistant_message(self, response: str) -> None:
        self.messages.append({"role": "assistant", "content": response})
        trim(self.messages, self.budget)

    def ask(self, client: OpenAI) -> str:
        response = client.chat.completions.create(
            model=os.environ["CHAT_MODEL"],
            messages=self.messages,
        )
        answer = response.choices[0].message.content or ""
        self.add_assistant_message(answer)
        return answer


def create_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_BASE_URL"],
    )


def ask_model(
    client: OpenAI,
    prompt: str,
    history: ConversationHistory | None = None,
) -> str:
    conversation = history or ConversationHistory()
    conversation.add_user_message(prompt)
    return conversation.ask(client)


def compare_prompts(client: OpenAI) -> None:
    prompts = [
        "Explain our refund policy.",
        "In one sentence, state the refund window in days.",
    ]
    for prompt in prompts:
        print(f"{prompt} -> {ask_model(client, prompt)}")


def validate_env() -> None:
    load_dotenv()
    missing = []

    for key, label in REQUIRED_ENV.items():
        value = os.getenv(key, "").strip()
        if not value or value in {"changeme", "replace-me", "set-me"}:
            missing.append(f"{label} ({key})")

    if missing:
        raise RuntimeError(
            "Missing or placeholder environment values: " + ", ".join(missing)
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run prompt construction examples.")
    parser.add_argument(
        "--prompt",
        help="Send one user prompt to the configured chat model.",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare a vague prompt with a constrained prompt.",
    )
    args = parser.parse_args()
    try:
        validate_env()
    except RuntimeError as exc:
        print(f"Environment configuration error: {exc}")
        return 1

    if args.prompt and args.compare:
        parser.error("--prompt and --compare cannot be used together")

    if args.prompt or args.compare:
        client = create_client()
    else:
        print("Environment is configured for the RAG app.")
        print(f"Chat model: {os.getenv('CHAT_MODEL')}")
        print(f"Embedding model: {os.getenv('EMBED_MODEL')}")
        return 0

    if args.compare:
        compare_prompts(client)
    else:
        print(ask_model(client, args.prompt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
