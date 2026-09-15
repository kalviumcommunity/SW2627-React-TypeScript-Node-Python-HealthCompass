"""Local document inspection command; emits JSON and requires no API credentials."""

import argparse
import json
import sys
from dataclasses import asdict

from .chunking import DEFAULT_MAX_CHARS, chunk_document
from .cleaning import clean_page
from .loader import DocumentLoadError, load_document


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract TXT, Markdown, HTML, or text-based PDF as JSON."
    )
    parser.add_argument("path", help="Local document path")
    parser.add_argument("--metadata", default="{}", help="JSON object with string keys and values")
    parser.add_argument(
        "--clean", action="store_true", help="Include cleaned text and raw extraction"
    )
    parser.add_argument(
        "--remove-boilerplate-line",
        action="append",
        default=[],
        help="Exact header/footer line to remove at page boundaries; repeatable",
    )
    parser.add_argument("--chunk", action="store_true", help="Emit source-traceable chunks as JSON")
    parser.add_argument("--chunk-strategy", choices=["fixed", "paragraph"])
    parser.add_argument(
        "--max-chars", type=int, help="Maximum characters per chunk (default: 1000)"
    )
    args = parser.parse_args()
    if not args.chunk and (args.chunk_strategy is not None or args.max_chars is not None):
        parser.error("--chunk-strategy and --max-chars require --chunk")
    if args.remove_boilerplate_line and not args.clean:
        parser.error("--remove-boilerplate-line requires --clean")
    try:
        metadata = json.loads(args.metadata)
        if not isinstance(metadata, dict):
            raise DocumentLoadError("Metadata must be a JSON object.")
        pages = load_document(args.path, metadata=metadata)
        if args.clean:
            pages = [
                clean_page(page, boilerplate_lines=args.remove_boilerplate_line) for page in pages
            ]
        if args.chunk:
            pages = chunk_document(
                pages,
                strategy=args.chunk_strategy or "paragraph",
                max_chars=args.max_chars if args.max_chars is not None else DEFAULT_MAX_CHARS,
            )
    except ValueError as exc:
        print(f"Document loading error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps([asdict(page) for page in pages], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
