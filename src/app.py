import argparse
import os
import sys

from dotenv import load_dotenv
from openai import APIError, OpenAI

from healthcompass.chat.history import (
    DEFAULT_CONTEXT_BUDGET,
    DEFAULT_OUTPUT_TOKENS,
    SYSTEM_PROMPT,
    ConversationHistory,
)

REQUIRED_ENV = {
    "OPENAI_BASE_URL": "OpenAI base URL",
    "OPENAI_API_KEY": "OpenAI API key",
    "CHAT_MODEL": "Chat model",
    "EMBED_MODEL": "Embedding model",
}


def build_messages(user_prompt: str, system_prompt: str = SYSTEM_PROMPT) -> list[dict[str, str]]:
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


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
    previous = [message.copy() for message in conversation.messages]
    try:
        conversation.add_user_message(prompt)
        return conversation.ask(client)
    except Exception:
        # A failed request must not leave a pending user message or lose history.
        conversation.messages = previous
        raise


def compare_prompts(
    client: OpenAI,
    budget: int = DEFAULT_CONTEXT_BUDGET,
    max_output_tokens: int = DEFAULT_OUTPUT_TOKENS,
    token_limit_parameter: str = "max_completion_tokens",
) -> None:
    """Compare prompts with independent histories and identical request budgets."""
    prompts = [
        "Explain our refund policy.",
        "In one sentence, state the refund window in days.",
    ]
    for prompt in prompts:
        history = ConversationHistory(
            budget=budget,
            max_output_tokens=max_output_tokens,
            token_limit_parameter=token_limit_parameter,
        )
        print(f"{prompt} -> {ask_model(client, prompt, history)}")


def validate_env() -> None:
    load_dotenv()
    missing = []

    for key, label in REQUIRED_ENV.items():
        value = os.getenv(key, "").strip()
        if not value or value in {"changeme", "replace-me", "set-me"}:
            missing.append(f"{label} ({key})")

    if missing:
        raise RuntimeError("Missing or placeholder environment values: " + ", ".join(missing))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run prompt construction examples.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--prompt",
        help="Send one user prompt to the configured chat model.",
    )
    modes.add_argument(
        "--compare",
        action="store_true",
        help="Compare a vague prompt with a constrained prompt.",
    )
    modes.add_argument(
        "--chat", action="store_true", help="Interactive multi-turn chat; /exit to quit"
    )
    parser.add_argument("--context-budget", type=int, default=DEFAULT_CONTEXT_BUDGET)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_OUTPUT_TOKENS)
    parser.add_argument(
        "--token-limit-parameter",
        choices=["max_completion_tokens", "max_tokens"],
        default="max_completion_tokens",
    )
    args = parser.parse_args()
    try:
        validate_env()
    except RuntimeError as exc:
        print(f"Environment configuration error: {exc}", file=sys.stderr)
        return 1

    try:
        history = ConversationHistory(
            budget=args.context_budget,
            max_output_tokens=args.max_output_tokens,
            token_limit_parameter=args.token_limit_parameter,
        )
        if args.prompt is not None or args.compare or args.chat:
            client = create_client()
        else:
            print("Environment is configured for the RAG app.")
            print(f"Chat model: {os.getenv('CHAT_MODEL')}")
            print(f"Embedding model: {os.getenv('EMBED_MODEL')}")
            return 0
        if args.chat:
            while True:
                try:
                    prompt = input("You: ")
                except (EOFError, KeyboardInterrupt):
                    break
                if prompt.strip() == "/exit":
                    break
                if prompt.strip():
                    print(ask_model(client, prompt, history))
        elif args.compare:
            compare_prompts(
                client, args.context_budget, args.max_output_tokens, args.token_limit_parameter
            )
        else:
            print(ask_model(client, args.prompt, history))
    except APIError as exc:
        print(
            f"Chat request failed ({type(exc).__name__}); check provider configuration.",
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        print(f"Chat request error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
