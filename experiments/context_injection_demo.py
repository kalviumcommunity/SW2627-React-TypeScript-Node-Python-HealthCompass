"""Demonstration of context injection and prompt augmentation."""

import os
from pathlib import Path

from healthcompass.rag import (
    assemble_context,
    build_augmented_prompt,
    format_chunk_with_source,
    get_max_context_tokens,
)
from healthcompass.vector_store import RetrievalResult, initialize_vector_store


def retrieve_with_deterministic_embeddings(query: str, k: int, collection):
    """Retrieve chunks using deterministic embeddings for demonstration.

    Args:
        query: User query
        k: Number of results to retrieve
        collection: ChromaDB collection

    Returns:
        List of RetrievalResult objects
    """
    # Create deterministic embedding based on query hash
    query_hash = hash(query) % 1000
    dimension = 1536  # text-embedding-3-small
    query_embedding = [0.001 * (query_hash + j) for j in range(dimension)]

    # Perform similarity search with deterministic embedding
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Process results into RetrievalResult objects
    retrieved_chunks = []
    for i, (doc_id, text, metadata, distance) in enumerate(
        zip(
            results["ids"][0] if results["ids"] else [],
            results["documents"][0] if results["documents"] else [],
            results["metadatas"][0] if results["metadatas"] else [],
            results["distances"][0] if results["distances"] else [],
            strict=True,
        )
    ):
        retrieved_chunks.append(
            RetrievalResult(
                rank=i + 1,
                chunk_id=doc_id,
                distance=distance,
                text=text,
                metadata=metadata,
            )
        )

    return retrieved_chunks


def demonstrate_context_injection():
    """Demonstrate context injection with actual retrieved chunks."""
    print("=== Context Injection Demonstration ===\n")

    # Initialize vector database
    collection = initialize_vector_store()
    print("Collection: healthcompass_documents")
    print("Database: data/chroma_db\n")

    # Sample question
    question = "What are the priority groups for vaccination?"
    print(f"Question: {question}\n")

    # Use deterministic embeddings if no API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("NOTE: Using deterministic embeddings for demonstration (no API key available).")
        print("      Results may not reflect actual semantic similarity.\n")
        retrieved_chunks = retrieve_with_deterministic_embeddings(question, 5, collection)
    else:
        from healthcompass.vector_store import retrieve

        retrieved_chunks = retrieve(question, k=5, collection=collection)

    print(f"Retrieved chunks: {len(retrieved_chunks)}\n")

    # Show retrieved chunks
    print("Retrieved Chunks:")
    for result in retrieved_chunks:
        source = result.metadata.get("source", "unknown")
        chunk_id = result.metadata.get("chunk_id", "unknown")
        print(f"  Rank {result.rank}: {result.chunk_id}")
        print(f"    Source: {source}")
        print(f"    Chunk ID: {chunk_id}")
        print(f"    Distance: {result.distance:.4f}")
        print(f"    Text: {result.text[:100]}...")
        print()

    # Demonstrate with a small token budget to show exclusion behavior
    small_budget = 300
    print(f"=== Token Budget Demonstration (max: {small_budget} tokens) ===\n")

    assembly_result = assemble_context(retrieved_chunks, max_context_tokens=small_budget)

    print(f"Retrieved chunks: {len(retrieved_chunks)}")
    print(f"Included chunks: {assembly_result.chunks_used}")
    print(f"Excluded chunks: {assembly_result.chunks_excluded}")
    print(f"Context tokens: {assembly_result.context_tokens} / {small_budget}")
    print()

    print("Sources used:")
    for source_info in assembly_result.sources_used:
        print(f"  [{source_info['rank']}] {source_info['source']}#{source_info['chunk_index']}")
    print()

    if assembly_result.chunks_excluded > 0:
        print(
            f"Excluded: {assembly_result.chunks_excluded} chunks because they exceeded the context budget."
        )
    print()

    # Demonstrate with normal token budget
    normal_budget = get_max_context_tokens()
    print(f"=== Normal Token Budget (max: {normal_budget} tokens) ===\n")

    assembly_result_normal = assemble_context(retrieved_chunks, max_context_tokens=normal_budget)

    print(f"Retrieved chunks: {len(retrieved_chunks)}")
    print(f"Included chunks: {assembly_result_normal.chunks_used}")
    print(f"Excluded chunks: {assembly_result_normal.chunks_excluded}")
    print(f"Context tokens: {assembly_result_normal.context_tokens} / {normal_budget}")
    print()

    # Demonstrate source markers
    print("=== Source Marker Demonstration ===\n")
    print("Formatted chunks with source markers:")
    for result in retrieved_chunks[:2]:  # Show first 2 for brevity
        formatted = format_chunk_with_source(result)
        print(f"{formatted[:150]}...")
        print()

    # Demonstrate augmented prompt
    print("=== Augmented Prompt Demonstration ===\n")

    prompt_result = build_augmented_prompt(
        question, retrieved_chunks, max_context_tokens=normal_budget
    )

    print(f"Context tokens: {prompt_result.context_tokens}")
    print(f"Chunks used: {prompt_result.chunks_used}")
    print(f"Chunks excluded: {prompt_result.chunks_excluded}")
    print()

    print("Augmented Prompt (first 500 characters):")
    print(prompt_result.prompt[:500] + "...")
    print()

    # Save results to file
    save_demonstration_results(
        question, retrieved_chunks, assembly_result_normal, prompt_result, normal_budget
    )


def save_demonstration_results(
    question, retrieved_chunks, assembly_result, prompt_result, max_budget
):
    """Save demonstration results to a markdown file.

    Args:
        question: The user question
        retrieved_chunks: List of retrieved chunks
        assembly_result: Context assembly result
        prompt_result: Augmented prompt result
        max_budget: Maximum context token budget
    """
    output_dir = Path("experiments/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "context_injection_results.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Context Injection Results\n\n")

        f.write("## Sample Question\n\n")
        f.write(f"{question}\n\n")

        f.write("## Retrieved Chunks\n\n")
        for result in retrieved_chunks:
            f.write(f"**Rank {result.rank}:** {result.chunk_id}\n")
            f.write(f"- Source: {result.metadata.get('source', 'unknown')}\n")
            f.write(f"- Chunk ID: {result.metadata.get('chunk_id', 'unknown')}\n")
            f.write(f"- Distance: {result.distance:.4f}\n")
            f.write(f"- Text: {result.text[:150]}...\n\n")

        f.write("## Assembled Context\n\n")
        f.write("```\n")
        f.write(assembly_result.context)
        f.write("\n```\n\n")

        f.write("## Token Budget\n\n")
        f.write(f"- Maximum context tokens: {max_budget}\n")
        f.write(f"- Tokens used: {assembly_result.context_tokens}\n")
        f.write(f"- Chunks included: {assembly_result.chunks_used}\n")
        f.write(f"- Chunks excluded: {assembly_result.chunks_excluded}\n\n")

        f.write("## Augmented Prompt\n\n")
        f.write("```\n")
        f.write(prompt_result.prompt)
        f.write("\n```\n\n")

        f.write("## Sources Used\n\n")
        for source_info in assembly_result.sources_used:
            f.write(
                f"- [{source_info['rank']}] {source_info['source']}#{source_info['chunk_index']}\n"
            )
            f.write(f"  - Chunk ID: {source_info['chunk_id']}\n")
            f.write(f"  - Distance: {source_info['distance']:.4f}\n\n")

        # Add note about deterministic embeddings if applicable
        if not os.getenv("OPENAI_API_KEY"):
            f.write(
                "**Note:** This demonstration used deterministic embeddings for testing without an API key.\n"
            )
            f.write("Retrieval results may not reflect actual semantic similarity.\n")

    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    demonstrate_context_injection()
