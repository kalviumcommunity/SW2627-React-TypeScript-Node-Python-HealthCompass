"""Local document inspection command; emits JSON and requires no API credentials."""

import argparse
from dataclasses import asdict
import json
import sys

from .loader import DocumentLoadError, load_document


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract TXT or text-based PDF as JSON.")
    parser.add_argument("path", help="Local document path")
    parser.add_argument("--metadata", default="{}", help="JSON object with string keys and values")
    args = parser.parse_args()
    try:
        metadata = json.loads(args.metadata)
        if not isinstance(metadata, dict):
            raise DocumentLoadError("Metadata must be a JSON object.")
        pages = load_document(args.path, metadata=metadata)
    except (DocumentLoadError, json.JSONDecodeError) as exc:
        print(f"Document loading error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps([asdict(page) for page in pages], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
