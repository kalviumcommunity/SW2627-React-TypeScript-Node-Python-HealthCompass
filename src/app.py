import os

from dotenv import load_dotenv


REQUIRED_ENV = {
    "OPENAI_BASE_URL": "OpenAI base URL",
    "OPENAI_API_KEY": "OpenAI API key",
    "CHAT_MODEL": "Chat model",
    "EMBED_MODEL": "Embedding model",
}


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
    try:
        validate_env()
    except RuntimeError as exc:
        print(f"Environment configuration error: {exc}")
        return 1

    print("Environment is configured for the RAG app.")
    print(f"Chat model: {os.getenv('CHAT_MODEL')}")
    print(f"Embedding model: {os.getenv('EMBED_MODEL')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
