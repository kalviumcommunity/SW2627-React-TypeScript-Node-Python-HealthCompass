"""Generate embeddings for HealthCompass document chunks."""

import json
import sys
from pathlib import Path

from healthcompass.ingestion import (
    EmbeddingError,
    generate_embeddings,
    prepare_chunks_from_token_chunks,
    token_chunks,
)


def create_sample_corpus() -> list[dict]:
    """Create a small sample corpus from vaccination guidance text."""
    sample_text = """
Vaccination Guidelines for Public Health Response

This document provides current approved guidance for vaccination protocols in public health emergencies. HealthCompass stores official public-health documents with versions, effective dates, geographic applicability, and approval status. Active and approved guidance should be preferred over superseded or expired documents.

Section 1: Core Vaccination Principles

Vaccination guidance should always be checked against the latest approved official version. Public health officials recommend following current guidelines from authoritative sources such as the CDC and WHO. Regular updates ensure that vaccination policies reflect the most recent scientific evidence and epidemiological data.

Healthcare providers must verify the approval status and effective dates of all vaccination protocols before implementation. Regional guidance may vary based on local epidemiological conditions and vaccine availability. Version control is essential for tracking policy changes and ensuring compliance with current standards.

Section 2: Priority Groups

High-risk populations include healthcare workers, elderly individuals, and those with underlying health conditions. These groups should be prioritized for vaccination according to current availability and epidemiological risk assessments.
    """.strip()

    # Use token-aware chunking to create chunks
    token_chunk_list = token_chunks(
        sample_text,
        source="vaccination_guidance_sample.txt",
        filename="vaccination_guidance_sample.txt",
        size=100,  # Small chunks for demonstration
        overlap=20,
        metadata={"section": "General Guidance", "version": "1.0"},
    )

    # Convert to embedding format
    return prepare_chunks_from_token_chunks(token_chunk_list)


def save_embedded_chunks(result, output_path: Path):
    """Save embedded chunks to JSON file."""
    serializable_chunks = []
    for chunk in result.embedded_chunks:
        serializable_chunks.append(
            {
                "text": chunk.text,
                "source": chunk.source,
                "filename": chunk.filename,
                "chunk_id": chunk.chunk_id,
                "metadata": chunk.metadata,
                "embedding": chunk.embedding,
                "embedding_model": chunk.embedding_model,
            }
        )

    output_data = {
        "manifest": {
            "embedding_model": result.manifest.embedding_model,
            "chunk_count": result.manifest.chunk_count,
            "vector_dimension": result.manifest.vector_dimension,
            "created_at": result.manifest.created_at,
            "source_files": result.manifest.source_files,
        },
        "chunks": serializable_chunks,
        "validation": {
            "passed": result.validation_passed,
            "errors": result.validation_errors,
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)


def generate_sample_report(result, output_path: Path):
    """Generate a human-readable sample report."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Embedding Generation Sample Report\n\n")
        f.write("## Configuration\n\n")
        f.write(f"**Embedding model:** {result.manifest.embedding_model}\n")
        f.write(f"**Chunks embedded:** {result.manifest.chunk_count}\n")
        f.write(f"**Vector dimension:** {result.manifest.vector_dimension}\n")
        f.write(f"**Created at:** {result.manifest.created_at}\n")
        f.write(f"**Source files:** {', '.join(result.manifest.source_files)}\n\n")

        f.write("## Validation\n\n")
        if result.validation_passed:
            f.write("✅ **Validation passed**\n\n")
        else:
            f.write("❌ **Validation failed**\n\n")
            for error in result.validation_errors:
                f.write(f"- {error}\n")
            f.write("\n")

        f.write("## Sample Records\n\n")

        # Show first 3 chunks
        sample_count = min(3, len(result.embedded_chunks))
        for i in range(sample_count):
            chunk = result.embedded_chunks[i]
            f.write(f"### Chunk {i}\n\n")
            f.write(f"**Source:** {chunk.source}\n")
            f.write(f"**Filename:** {chunk.filename}\n")
            f.write(f"**Chunk ID:** {chunk.chunk_id}\n")
            f.write(f"**Vector length:** {len(chunk.embedding)}\n")
            f.write(f"**Metadata:** {json.dumps(chunk.metadata)}\n\n")
            f.write("**Text:**\n")
            f.write(f"```\n{chunk.text}\n```\n\n")
            f.write("**Sample vector values (first 5):**\n")
            f.write(f"```\n{chunk.embedding[:5]}\n```\n\n")

        if len(result.embedded_chunks) > sample_count:
            f.write(f"... ({len(result.embedded_chunks) - sample_count} additional chunks omitted)\n\n")

        f.write("## Cost and Performance Considerations\n\n")
        f.write("- Embedding generation requires API calls for each batch of chunks\n")
        f.write("- Cost scales with the number of chunks and vector dimension\n")
        f.write("- Latency increases with corpus size and batch size\n")
        f.write("- Batching reduces API overhead but increases per-request complexity\n")
        f.write("- Larger vector dimensions improve semantic representation but increase storage and computation cost\n\n")


def main():
    """Main entry point for embedding generation."""
    print("=" * 70)
    print("HealthCompass Embedding Generation")
    print("=" * 70)
    print()

    # Create sample corpus
    print("Creating sample corpus from vaccination guidance...")
    chunks = create_sample_corpus()
    print(f"Created {len(chunks)} chunks for embedding")
    print()

    # Generate embeddings
    print("Generating embeddings via API...")
    try:
        result = generate_embeddings(chunks, batch_size=10)
        print(f"[OK] Successfully generated {len(result.embedded_chunks)} embeddings")
        print(f"   Model: {result.manifest.embedding_model}")
        print(f"   Vector dimension: {result.manifest.vector_dimension}")
        print()

        # Validation results
        if result.validation_passed:
            print("[OK] Validation passed")
        else:
            print("[FAIL] Validation failed:")
            for error in result.validation_errors:
                print(f"   - {error}")
        print()

        # Sample output
        print("Sample chunk:")
        if result.embedded_chunks:
            sample = result.embedded_chunks[0]
            print(f"  Source: {sample.source}")
            print(f"  Chunk ID: {sample.chunk_id}")
            print(f"  Text: {sample.text[:100]}...")
            print(f"  Vector length: {len(sample.embedding)}")
            print(f"  Sample values: {sample.embedding[:3]}")
        print()

        # Save outputs
        output_dir = Path("experiments/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / "embedded_chunks.json"
        save_embedded_chunks(result, json_path)
        print(f"Saved embedded chunks to: {json_path}")

        report_path = output_dir / "embedding_sample.md"
        generate_sample_report(result, report_path)
        print(f"Saved sample report to: {report_path}")

    except EmbeddingError as e:
        print(f"[ERROR] Embedding generation failed: {e}")
        print()
        print("Note: This is expected if OPENAI_API_KEY is not configured.")
        print("The embedding code is implemented and tested with mocked responses.")
        print("To run with real API calls, configure your API key in .env file.")
        sys.exit(1)


if __name__ == "__main__":
    main()
