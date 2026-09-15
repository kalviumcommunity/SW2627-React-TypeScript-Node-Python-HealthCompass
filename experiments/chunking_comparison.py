"""Compare chunk sizes and paragraph preservation offline; no retrieval quality claims."""

import argparse
import json
import re
from pathlib import Path

from healthcompass.ingestion import chunk_page, clean_page, load_document


def compare(path: str | Path, max_chars: int = 160) -> dict:
    pages = [clean_page(page) for page in load_document(path)]
    measurements = []
    for strategy in ("fixed", "paragraph"):
        sizes = []
        paragraph_count = split_count = 0
        for page in pages:
            chunks = chunk_page(page, strategy=strategy, max_chars=max_chars)
            sizes.extend(len(chunk.text) for chunk in chunks)
            # Evaluate paragraph preservation independently of the chunk boundary implementation.
            offset = 0
            for paragraph in re.split(r"\n[ \t]*\n+", page.text):
                if not paragraph.strip():
                    continue
                start = page.text.index(paragraph, offset)
                end = start + len(paragraph.rstrip())
                start += len(paragraph) - len(paragraph.lstrip())
                offset = end
                paragraph_count += 1
                if not any(chunk.start_char <= start and chunk.end_char >= end for chunk in chunks):
                    split_count += 1
        measurements.append(
            {
                "strategy": strategy,
                "chunk_count": len(sizes),
                "min_chars": min(sizes, default=0),
                "max_chars": max(sizes, default=0),
                "mean_chars": round(sum(sizes) / len(sizes), 2) if sizes else 0,
                "paragraph_count": paragraph_count,
                "split_paragraphs": split_count,
            }
        )
    return {
        "document_id": pages[0].document_id,
        "max_chars": max_chars,
        "input": "cleaned",
        "measurements": measurements,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--max-chars", type=int, default=160)
    args = parser.parse_args(argv)
    try:
        report = compare(args.path, args.max_chars)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
