"""Chunking strategy comparison for HealthCompass documents."""

import sys
from pathlib import Path

from healthcompass.ingestion import (
    ChunkingStats,
    calculate_chunk_stats,
    chunk_document,
    clean_page,
    load_document,
)


def format_comparison_table(fixed_stats: ChunkingStats, paragraph_stats: ChunkingStats) -> str:
    """Format a comparison table of chunking statistics."""
    table = "Strategy              Chunk Count    Avg Size    Min Size    Max Size\n"
    table += "--------------------------------------------------------------\n"
    table += f"Fixed-size + overlap  {fixed_stats.chunk_count:<14} {fixed_stats.avg_chunk_size:<10.0f} {fixed_stats.min_chunk_size:<10} {fixed_stats.max_chunk_size:<10}\n"
    table += f"Paragraph-based       {paragraph_stats.chunk_count:<14} {paragraph_stats.avg_chunk_size:<10.0f} {paragraph_stats.min_chunk_size:<10} {paragraph_stats.max_chunk_size:<10}\n"
    return table


def format_sample_chunks(chunks, strategy_name: str, max_samples: int = 3) -> str:
    """Format sample chunks for display."""
    output = f"# {strategy_name}\n\n"

    for chunk in chunks[:max_samples]:
        output += f"### Chunk {chunk.chunk_id}\n\n"
        output += f"**Length:** {len(chunk.text)} characters\n"
        output += f"**Source:** {chunk.filename}\n\n"
        output += f"```\n{chunk.text}\n```\n\n"

    if len(chunks) > max_samples:
        output += f"*... and {len(chunks) - max_samples} more chunks*\n\n"

    return output


def save_comparison_report(
    document_path: str,
    fixed_stats: ChunkingStats,
    paragraph_stats: ChunkingStats,
    fixed_chunks: list,
    paragraph_chunks: list,
    output_path: str,
):
    """Save comprehensive chunking comparison report."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Chunking Strategy Comparison\n\n")
        f.write(f"**Document:** {document_path}\n\n")

        f.write("## Statistics Comparison\n\n")
        f.write(format_comparison_table(fixed_stats, paragraph_stats))
        f.write("\n")

        f.write("## Sample Chunks\n\n")
        f.write(format_sample_chunks(fixed_chunks, "Fixed-size + overlap"))
        f.write(format_sample_chunks(paragraph_chunks, "Paragraph-based"))

        f.write("## Trade-off Analysis\n\n")
        f.write("### Fixed-size + overlap\n\n")
        f.write("**Advantages:**\n")
        f.write("- Predictable chunk sizes\n")
        f.write("- Works well with long documents\n")
        f.write("- Overlap helps preserve context across boundaries\n")
        f.write("- Useful when paragraphs are extremely long or inconsistent\n\n")
        f.write("**Disadvantages:**\n")
        f.write("- Can split sentences/paragraphs\n")
        f.write("- May reduce semantic coherence\n")
        f.write("- Overlap creates some duplicated text\n\n")

        f.write("### Paragraph-based\n\n")
        f.write("**Advantages:**\n")
        f.write("- Preserves natural semantic boundaries\n")
        f.write("- Easier for humans to inspect\n")
        f.write("- Paragraphs usually represent a coherent idea\n\n")
        f.write("**Disadvantages:**\n")
        f.write("- Chunk sizes can vary significantly\n")
        f.write("- Very long paragraphs may still exceed useful retrieval size\n")
        f.write("- Very short paragraphs can produce tiny chunks\n\n")

        f.write("## Recommended Strategy\n\n")

        # Analyze the actual results to make a recommendation
        if paragraph_stats.max_chunk_size > 1000:
            recommendation = "Fixed-size + overlap"
            reason = "The document contains very long paragraphs that would exceed useful retrieval size for vector search."
        elif paragraph_stats.min_chunk_size < 50:
            recommendation = "Fixed-size + overlap"
            reason = "The document contains very short paragraphs (minimum: {} chars) that would produce tiny chunks lacking context for effective retrieval.".format(
                paragraph_stats.min_chunk_size
            )
        elif paragraph_stats.avg_chunk_size > 800:
            recommendation = "Fixed-size + overlap"
            reason = "Average paragraph size is large ({} chars), which could reduce retrieval precision in vector search.".format(
                int(paragraph_stats.avg_chunk_size)
            )
        else:
            recommendation = "Paragraph-based"
            reason = "The document has well-structured paragraphs of reasonable size (avg: {} chars, max: {} chars), preserving semantic coherence for better retrieval quality.".format(
                int(paragraph_stats.avg_chunk_size), paragraph_stats.max_chunk_size
            )

        f.write(f"**Recommended strategy:** {recommendation}\n\n")
        f.write(f"**Reason:** {reason}\n\n")

        f.write("## Context Window Relationship\n\n")
        f.write("Chunk size relates to the context window in several important ways:\n\n")
        f.write(
            "- The context window is the maximum amount of text/tokens the model can process in one request\n"
        )
        f.write(
            "- Chunks should be small enough that multiple retrieved chunks plus the user's question and system instructions fit comfortably\n"
        )
        f.write("- Very large chunks waste context space and can reduce retrieval precision\n")
        f.write("- Very small chunks may lose necessary context\n")
        f.write(
            "- Chunk size should therefore leave room for multiple relevant chunks and the generated answer\n\n"
        )
        f.write(
            "For HealthCompass, with typical context windows of 4K-8K tokens, chunk sizes of 500-1000 characters balance context preservation with retrieval precision."
        )


def main():
    if len(sys.argv) != 2:
        print("Usage: python chunking_comparison.py <document_path>")
        return 1

    document_path = sys.argv[1]

    try:
        # Load and clean the document
        pages = load_document(document_path)
        if not pages:
            print("Error: No pages loaded from document")
            return 1

        # Clean the document (use first page for single-page docs)
        cleaned_page = clean_page(pages[0])

        # Apply both chunking strategies
        fixed_chunks = chunk_document(cleaned_page, strategy="fixed", chunk_size=500, overlap=100)
        paragraph_chunks = chunk_document(cleaned_page, strategy="paragraph")

        # Calculate statistics
        fixed_stats = calculate_chunk_stats(fixed_chunks)
        paragraph_stats = calculate_chunk_stats(paragraph_chunks)

        # Print summary
        print("Chunking Comparison Results")
        print("=" * 50)
        print(format_comparison_table(fixed_stats, paragraph_stats))
        print()

        # Save detailed report
        output_dir = Path("experiments/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "chunking_comparison.md"

        save_comparison_report(
            document_path,
            fixed_stats,
            paragraph_stats,
            fixed_chunks,
            paragraph_chunks,
            str(output_path),
        )

        print(f"Detailed report saved to: {output_path}")
        print()
        print("Sample Fixed-size Chunks:")
        print("-" * 30)
        for chunk in fixed_chunks[:2]:
            print(f"Chunk {chunk.chunk_id}: {len(chunk.text)} chars | '{chunk.text[:60]}...'")

        print()
        print("Sample Paragraph Chunks:")
        print("-" * 30)
        for chunk in paragraph_chunks[:2]:
            print(f"Chunk {chunk.chunk_id}: {len(chunk.text)} chars | '{chunk.text[:60]}...'")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
