"""Token-aware chunking comparison with boundary-context demonstration."""

import sys
from pathlib import Path

from healthcompass.ingestion import calculate_token_chunk_stats, token_chunks


def demonstrate_boundary_context():
    """Demonstrate how overlap preserves context across chunk boundaries."""
    print("=" * 70)
    print("BOUNDARY-CONTEXT DEMONSTRATION")
    print("=" * 70)
    print()

    # Create a controlled example where an important sentence crosses a boundary
    boundary_text = """
Vaccination protocols require strict adherence to approved guidelines. 
Healthcare providers must verify that all vaccination protocols are followed 
according to the latest approved official version from public health authorities. 
Regular updates ensure that vaccination policies reflect the most recent scientific 
evidence and epidemiological data available from the CDC and WHO.
    """.strip()

    print("Controlled text for boundary demonstration:")
    print("-" * 70)
    print(boundary_text)
    print("-" * 70)
    print()

    # Demonstrate without overlap
    print("WITHOUT OVERLAP (overlap = 0)")
    print("-" * 70)
    chunks_no_overlap = token_chunks(
        boundary_text,
        source="boundary_demo.txt",
        filename="boundary_demo.txt",
        size=40,  # Small size to force boundary crossing
        overlap=0,
    )

    for i, chunk in enumerate(chunks_no_overlap):
        print(f"Chunk {i}:")
        print(f"  Token count: {chunk.token_count}")
        print(f"  Text: {chunk.text}")
        print()

    # Demonstrate with overlap
    print("WITH OVERLAP (overlap = 10)")
    print("-" * 70)
    chunks_with_overlap = token_chunks(
        boundary_text,
        source="boundary_demo.txt",
        filename="boundary_demo.txt",
        size=40,  # Same size for fair comparison
        overlap=10,
    )

    for i, chunk in enumerate(chunks_with_overlap):
        print(f"Chunk {i}:")
        print(f"  Token count: {chunk.token_count}")
        print(f"  Text: {chunk.text}")
        print()

    print("=" * 70)
    print("OBSERVATION:")
    print("=" * 70)
    print("Without overlap, important information crossing the boundary is split")
    print("between chunks, potentially losing context for retrieval.")
    print()
    print("With overlap, the boundary context appears in both neighboring chunks,")
    print("ensuring that critical information is preserved for retrieval.")
    print()


def run_comparison(document_path: str):
    """Run token-based chunking comparison on a document."""
    print("=" * 70)
    print("TOKEN-AWARE CHUNKING COMPARISON")
    print("=" * 70)
    print()

    # Read the document
    with open(document_path, "r", encoding="utf-8") as f:
        text = f.read()

    source_path = Path(document_path).name
    print(f"Document: {source_path}")
    print(f"Total characters: {len(text)}")
    print()

    # Configuration
    chunk_size = 400
    overlap = 60
    encoding_name = "cl100k_base"

    print("Configuration:")
    print("-" * 70)
    print(f"Chunk size: {chunk_size} tokens")
    print(f"Overlap: {overlap} tokens")
    print(f"Overlap percentage: {overlap / chunk_size * 100:.1f}%")
    print(f"Tokenizer: {encoding_name}")
    print()

    # Run without overlap
    print("Chunking WITHOUT overlap:")
    print("-" * 70)
    chunks_no_overlap = token_chunks(
        text,
        source=source_path,
        filename=source_path,
        size=chunk_size,
        overlap=0,
    )
    stats_no_overlap = calculate_token_chunk_stats(chunks_no_overlap)

    print(f"Number of chunks: {stats_no_overlap.chunk_count}")
    print(f"Total tokens: {stats_no_overlap.total_tokens}")
    print(f"Average tokens per chunk: {stats_no_overlap.avg_token_count:.1f}")
    print(f"Min tokens: {stats_no_overlap.min_token_count}")
    print(f"Max tokens: {stats_no_overlap.max_token_count}")
    print()

    # Run with overlap
    print("Chunking WITH overlap:")
    print("-" * 70)
    chunks_with_overlap = token_chunks(
        text,
        source=source_path,
        filename=source_path,
        size=chunk_size,
        overlap=overlap,
    )
    stats_with_overlap = calculate_token_chunk_stats(chunks_with_overlap)

    print(f"Number of chunks: {stats_with_overlap.chunk_count}")
    print(f"Total tokens: {stats_with_overlap.total_tokens}")
    print(f"Average tokens per chunk: {stats_with_overlap.avg_token_count:.1f}")
    print(f"Min tokens: {stats_with_overlap.min_token_count}")
    print(f"Max tokens: {stats_with_overlap.max_token_count}")
    print()

    # Comparison table
    print("=" * 70)
    print("COMPARISON TABLE")
    print("=" * 70)
    print(f"{'Strategy':<25} {'Chunks':<10} {'Avg Tokens':<15} {'Total Tokens':<15}")
    print("-" * 70)
    print(f"{'No overlap':<25} {stats_no_overlap.chunk_count:<10} {stats_no_overlap.avg_token_count:<15.1f} {stats_no_overlap.total_tokens:<15}")
    print(f"{'{overlap}-token overlap':<25} {stats_with_overlap.chunk_count:<10} {stats_with_overlap.avg_token_count:<15.1f} {stats_with_overlap.total_tokens:<15}".format(overlap=overlap))
    print()

    # Cost comparison
    print("=" * 70)
    print("COST COMPARISON")
    print("=" * 70)
    additional_chunks = stats_with_overlap.chunk_count - stats_no_overlap.chunk_count
    additional_tokens = stats_with_overlap.total_tokens - stats_no_overlap.total_tokens
    print(f"Additional chunks with overlap: {additional_chunks}")
    print(f"Additional tokens with overlap: {additional_tokens}")
    print(f"Percentage increase in tokens: {additional_tokens / stats_no_overlap.total_tokens * 100:.1f}%")
    print()
    print("Trade-off: Overlap increases storage and retrieval cost by adding")
    print("repeated tokens, but improves context preservation across boundaries.")
    print()

    # Sample chunks
    print("=" * 70)
    print("SAMPLE CHUNKS (with overlap)")
    print("=" * 70)
    print()

    sample_count = min(3, len(chunks_with_overlap))
    for i in range(sample_count):
        chunk = chunks_with_overlap[i]
        print(f"Chunk {i}:")
        print("-" * 70)
        print(f"Token count: {chunk.token_count}")
        print(f"Source: {chunk.source}")
        print()
        print(chunk.text)
        print()

    if len(chunks_with_overlap) > sample_count:
        print(f"... ({len(chunks_with_overlap) - sample_count} additional chunks omitted)")
        print()

    return {
        "no_overlap": stats_no_overlap,
        "with_overlap": stats_with_overlap,
        "chunks_no_overlap": chunks_no_overlap,
        "chunks_with_overlap": chunks_with_overlap,
    }


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python token_chunking_comparison.py <document_path>")
        sys.exit(1)

    document_path = sys.argv[1]

    # First demonstrate boundary context
    demonstrate_boundary_context()

    print("\n\n")

    # Then run full comparison
    results = run_comparison(document_path)

    # Generate report
    report_path = Path("experiments/outputs/token_chunking_comparison.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Token-Aware Chunking Comparison\n\n")
        f.write("## Configuration\n\n")
        f.write(f"- Chunk size: 400 tokens\n")
        f.write(f"- Overlap: 60 tokens\n")
        f.write(f"- Overlap percentage: 15.0%\n")
        f.write(f"- Tokenizer: cl100k_base\n\n")

        f.write("## Chunk Statistics\n\n")
        f.write(f"| Strategy | Chunks | Avg Tokens | Min Tokens | Max Tokens | Total Tokens |\n")
        f.write(f"|----------|--------|------------|------------|------------|--------------|\n")
        f.write(
            f"| No overlap | {results['no_overlap'].chunk_count} | {results['no_overlap'].avg_token_count:.1f} | {results['no_overlap'].min_token_count} | {results['no_overlap'].max_token_count} | {results['no_overlap'].total_tokens} |\n"
        )
        f.write(
            f"| 60-token overlap | {results['with_overlap'].chunk_count} | {results['with_overlap'].avg_token_count:.1f} | {results['with_overlap'].min_token_count} | {results['with_overlap'].max_token_count} | {results['with_overlap'].total_tokens} |\n"
        )
        f.write("\n")

        f.write("## Cost Comparison\n\n")
        additional_chunks = results["with_overlap"].chunk_count - results["no_overlap"].chunk_count
        additional_tokens = results["with_overlap"].total_tokens - results["no_overlap"].total_tokens
        f.write(f"- Additional chunks with overlap: {additional_chunks}\n")
        f.write(f"- Additional tokens with overlap: {additional_tokens}\n")
        f.write(
            f"- Percentage increase in tokens: {additional_tokens / results['no_overlap'].total_tokens * 100:.1f}%\n"
        )
        f.write("\n")

        f.write("## Sample Chunks (with overlap)\n\n")
        sample_count = min(3, len(results["chunks_with_overlap"]))
        for i in range(sample_count):
            chunk = results["chunks_with_overlap"][i]
            f.write(f"### Chunk {i}\n\n")
            f.write(f"**Token count:** {chunk.token_count}\n\n")
            f.write(f"**Source:** {chunk.source}\n\n")
            f.write(f"```\n{chunk.text}\n```\n\n")

        if len(results["chunks_with_overlap"]) > sample_count:
            f.write(f"... ({len(results['chunks_with_overlap']) - sample_count} additional chunks omitted)\n\n")

        f.write("## Boundary-Context Demonstration\n\n")
        f.write("The demonstration shows how overlap preserves context across chunk boundaries.\n\n")
        f.write("Without overlap, important information crossing the boundary is split between chunks.\n\n")
        f.write("With overlap, the boundary context appears in both neighboring chunks, ensuring that critical information is preserved for retrieval.\n\n")

        f.write("## Context Window Considerations\n\n")
        f.write("Retrieved context roughly depends on:\n\n")
        f.write("```\nchunk_size × top_k\n```\n\n")
        f.write("Plus:\n")
        f.write("- System instructions\n")
        f.write("- User question\n")
        f.write("- Other prompt content\n")
        f.write("- Generated answer budget\n\n")
        f.write("Therefore:\n")
        f.write("- Increasing chunk size reduces how many chunks can fit comfortably\n")
        f.write("- Increasing top-k increases retrieved token count\n")
        f.write("- Increasing overlap increases repeated tokens\n")
        f.write("- Chunk size, overlap, top-k, and context window should be tuned together\n\n")

        f.write("## Justification\n\n")
        f.write("### Chunk Size (400 tokens)\n\n")
        f.write("- Tokens are the model's actual unit rather than characters\n")
        f.write("- 400 tokens provides a reasonably sized retrieval unit\n")
        f.write("- Multiple retrieved chunks can fit into a model context window together with the system prompt, user question, and answer\n")
        f.write("- Smaller chunks improve retrieval precision but may lose context\n")
        f.write("- Larger chunks preserve more context but can reduce retrieval precision and increase token/embedding cost\n\n")

        f.write("### Overlap (60 tokens)\n\n")
        f.write("- 60 tokens provides approximately 15% overlap\n")
        f.write("- Overlap helps preserve ideas that cross chunk boundaries\n")
        f.write("- Too much overlap duplicates text and increases embedding/storage/retrieval cost\n")
        f.write("- Too little overlap increases the risk of losing boundary context\n\n")

        f.write("### HealthCompass Document Considerations\n\n")
        f.write("- Public-health guidance documents often contain procedural instructions that span multiple sentences\n")
        f.write("- Vaccination protocols include detailed dosing schedules that should not be split arbitrarily\n")
        f.write("- Advisories and SOPs contain critical safety information that must be preserved across boundaries\n")
        f.write("- Policy documents may have long sections that benefit from overlap to maintain context\n\n")

    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
