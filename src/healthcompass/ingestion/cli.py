"""Local document inspection command; emits JSON and requires no API credentials."""

import argparse
from dataclasses import asdict
import json
import sys

from .cleaning import clean_page
from .loader import DocumentLoadError, load_document


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract TXT or text-based PDF as JSON.")
    parser.add_argument("path", help="Local document path")
    parser.add_argument("--metadata", default="{}", help="JSON object with string keys and values")
    parser.add_argument("--clean", action="store_true", help="Include cleaned text and raw extraction")
    parser.add_argument("--remove-boilerplate-line", action="append", default=[],
                        help="Exact header/footer line to remove at page boundaries; repeatable")
    args = parser.parse_args()
    if args.remove_boilerplate_line and not args.clean:
        parser.error("--remove-boilerplate-line requires --clean")
    try:
        metadata = json.loads(args.metadata)
        if not isinstance(metadata, dict):
            raise DocumentLoadError("Metadata must be a JSON object.")
        pages = load_document(args.path, metadata=metadata)
        if args.clean:
            pages = [clean_page(page, boilerplate_lines=args.remove_boilerplate_line) for page in pages]
    except ValueError as exc:
        print(f"Document loading error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps([asdict(page) for page in pages], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
