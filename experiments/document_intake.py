"""Document intake demo script for multi-format loading."""

import argparse
import sys
from pathlib import Path

from healthcompass.ingestion import DocumentLoadError, ingest_corpus, load_document


def print_intake_summary(result):
    """Print a formatted summary of corpus ingestion results."""
    print("\nDocument Intake Summary")
    print("------------------------")
    print(f"Loaded: {result.loaded_files} documents ({len(result.loaded)} pages)")
    print(f"Skipped: {len(result.skipped)} files")
    print(f"Total files processed: {result.total_files}")
    print()


def print_document_details(pages):
    """Print details for each loaded document."""
    for page in pages:
        text_length = len(page.text)
        text_preview = (
            page.text[:60].replace("\n", " ") if text_length > 60 else page.text.replace("\n", " ")
        )
        print(f"OK {page.filename}: {text_length} chars | '{text_preview}...'")


def print_skipped_files(skipped):
    """Print details of skipped files."""
    for filename, error in skipped:
        print(f"SKIP {filename}: {error}")


def demo_single_file(file_path):
    """Demo loading a single file."""
    try:
        pages = load_document(file_path)
        print(f"\nSuccessfully loaded: {file_path}")
        print_document_details(pages)
        return True
    except DocumentLoadError as exc:
        print(f"\nFailed to load {file_path}: {exc}")
        return False


def demo_corpus(directory):
    """Demo corpus ingestion from a directory."""
    try:
        result = ingest_corpus(directory)
        print_intake_summary(result)

        if result.loaded:
            print("Loaded Documents:")
            print("-----------------")
            # Group by filename to avoid duplicates
            by_source = {}
            for page in result.loaded:
                if page.source not in by_source:
                    by_source[page.source] = []
                by_source[page.source].append(page)

            for source, pages in by_source.items():
                text_length = sum(len(page.text) for page in pages)
                text_preview = (
                    pages[0].text[:60].replace("\n", " ")
                    if text_length > 60
                    else pages[0].text.replace("\n", " ")
                )
                print(f"OK {source}: {text_length} chars | '{text_preview}...'")

        if result.skipped:
            print("\nSkipped Files:")
            print("-------------")
            print_skipped_files(result.skipped)

        return bool(result.loaded) and not result.skipped
    except DocumentLoadError as exc:
        print(f"Corpus ingestion failed: {exc}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Document intake demo for multi-format loading")
    parser.add_argument("path", help="Path to document file or directory for corpus ingestion")
    parser.add_argument(
        "--corpus", action="store_true", help="Treat path as directory for corpus ingestion"
    )
    args = parser.parse_args()

    path = Path(args.path)

    if not path.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        return 1

    if args.corpus:
        if not path.is_dir():
            print(f"Error: Path is not a directory: {args.path}", file=sys.stderr)
            return 1
        success = demo_corpus(path)
    else:
        if path.is_dir():
            print(
                "Error: Path is a directory. Use --corpus flag for directory ingestion.",
                file=sys.stderr,
            )
            return 1
        success = demo_single_file(path)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
