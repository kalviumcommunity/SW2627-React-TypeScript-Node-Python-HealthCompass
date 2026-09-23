"""Similarity search and top-k retrieval demonstration for HealthCompass."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from healthcompass.vector_store import (
    RetrievalResult,
    get_collection_info,
    get_vector_store_config,
    initialize_vector_store,
    retrieve,
)


def format_retrieval_results(results, k_value):
    """Format retrieval results for display.

    Args:
        results: List of RetrievalResult objects
        k_value: The k value used for retrieval

    Returns:
        Formatted string for display
    """
    output = f"\nResults for k={k_value}:\n"
    output += "=" * 80 + "\n"

    if not results:
        output += "No results returned.\n"
        return output

    for result in results:
        output += f"\nRank: {result.rank}\n"
        output += f"Distance: {result.distance:.4f}\n"
        output += f"Chunk ID: {result.chunk_id}\n"
        output += f"Source: {result.metadata.get('source', 'N/A')}\n"
        output += f"Filename: {result.metadata.get('filename', 'N/A')}\n"
        output += f"Chunk Index: {result.metadata.get('chunk_id', 'N/A')}\n"
        output += f"Section: {result.metadata.get('section', 'N/A')}\n"
        output += f"Page Number: {result.metadata.get('page_number', 'N/A')}\n"
        output += f"Document Type: {result.metadata.get('document_type', 'N/A')}\n"
        output += f"Text: {result.text[:200]}...\n"  # Truncate for display
        output += "-" * 80 + "\n"

    return output


def main():
    """Main entry point for retrieval demonstration."""
    print("=" * 80)
    print("HealthCompass Similarity Search and Top-K Retrieval Demo")
    print("=" * 80)
    print()

    # Sample query relevant to HealthCompass
    sample_query = "How can a learner reset their password?"

    print(f"Sample Query: {sample_query}")
    print()

    # Get configuration
    print("Loading vector database configuration...")
    config = get_vector_store_config()
    print(f"Database path: {config.db_path}")
    print(f"Collection name: {config.collection_name}")
    print(f"Embedding dimension: {config.embedding_dimension}")
    print(f"Embedding model: {config.embedding_model}")
    print()

    # Initialize vector database
    print("Initializing vector database...")
    collection = initialize_vector_store(config)
    print()

    # Get collection info
    print("Collection information:")
    info = get_collection_info(collection)
    print(f"  Name: {info['name']}")
    print(f"  Record count: {info['count']}")
    print(f"  Vector dimension: {info['dimension']}")
    print()

    # Check if collection has records
    if info['count'] == 0:
        print("ERROR: Collection is empty. Please insert documents before running retrieval.")
        print("Run the vector_db_readback.py script to insert test records.")
        sys.exit(1)

    # Test different k values
    k_values = [1, 3, 5]

    print(f"Testing retrieval with k values: {k_values}")
    print()

    all_results = {}
    api_available = True

    for k in k_values:
        print(f"Retrieving top {k} results...")
        try:
            results = retrieve(
                query=sample_query,
                collection=collection,
                k=k,
                embedding_model=config.embedding_model,
            )
            all_results[k] = results
            print(f"Successfully retrieved {len(results)} results for k={k}")
        except Exception as e:
            if "OPENAI_API_KEY" in str(e):
                api_available = False
                print(f"API key not configured. Using mock data for demonstration.")
                # Generate mock results for demonstration based on available records
                num_results = min(k, info['count'])
                all_results[k] = [
                    RetrievalResult(
                        rank=i + 1,
                        chunk_id=f"chunk_{i}",
                        distance=0.1 + (i * 0.1),
                        text=f"Document chunk {i} - This is a test vaccination guidance document for HealthCompass public health response.",
                        metadata={
                            "source": "test_guidance.txt",
                            "filename": "test_guidance.txt",
                            "chunk_id": str(i),
                            "section": "Introduction",
                            "page_number": str(i + 1),
                            "document_type": "guidance",
                        }
                    )
                    for i in range(num_results)
                ]
                print(f"Generated {len(all_results[k])} mock results for k={k} (collection has {info['count']} records)")
            else:
                print(f"ERROR: Failed to retrieve results for k={k}: {e}")
                all_results[k] = []

    # Display results
    print()
    print("=" * 80)
    print("RETRIEVAL RESULTS")
    print("=" * 80)

    for k in k_values:
        print(format_retrieval_results(all_results[k], k))

    # Generate report
    output_dir = Path("experiments/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "retrieval_results.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Similarity Search and Top-K Retrieval Results\n\n")

        f.write("## Configuration\n\n")
        f.write(f"**Sample Query:** {sample_query}\n")
        f.write(f"**Database path:** {config.db_path}\n")
        f.write(f"**Collection name:** {config.collection_name}\n")
        f.write(f"**Embedding dimension:** {config.embedding_dimension}\n")
        f.write(f"**Embedding model:** {config.embedding_model}\n\n")

        if not api_available:
            f.write("**Note:** API key not configured. Results are mock data for demonstration purposes.\n\n")

        f.write("## Collection Information\n\n")
        f.write(f"**Name:** {info['name']}\n")
        f.write(f"**Record count:** {info['count']}\n")
        f.write(f"**Vector dimension:** {info['dimension']}\n")
        f.write(f"**Metadata:** {info['metadata']}\n\n")

        f.write("## Distance Score Explanation\n\n")
        f.write("The results use **cosine distance** as the similarity metric.\n\n")
        f.write("- **Lower distance values** indicate higher similarity (closer in semantic space)\n")
        f.write("- Distance range: 0.0 (identical) to 2.0 (opposite) for normalized vectors\n")
        f.write("- A distance of 0.0 means the query and chunk are semantically identical\n")
        f.write("- A distance around 0.3-0.5 typically indicates strong semantic similarity\n\n")

        f.write("## Retrieval Results by k Value\n\n")

        for k in k_values:
            f.write(f"### k={k}\n\n")
            f.write(f"**Number of results returned:** {len(all_results[k])}\n\n")

            if not all_results[k]:
                f.write("No results returned.\n\n")
                continue

            for result in all_results[k]:
                f.write(f"#### Rank {result.rank}\n\n")
                f.write(f"**Distance:** {result.distance:.4f}\n")
                f.write(f"**Chunk ID:** {result.chunk_id}\n")
                f.write(f"**Source:** {result.metadata.get('source', 'N/A')}\n")
                f.write(f"**Filename:** {result.metadata.get('filename', 'N/A')}\n")
                f.write(f"**Chunk Index:** {result.metadata.get('chunk_id', 'N/A')}\n")
                f.write(f"**Section:** {result.metadata.get('section', 'N/A')}\n")
                f.write(f"**Page Number:** {result.metadata.get('page_number', 'N/A')}\n")
                f.write(f"**Document Type:** {result.metadata.get('document_type', 'N/A')}\n")
                f.write(f"**Text:** {result.text}\n\n")

        f.write("## Analysis\n\n")
        f.write("### Effect of k on Results\n\n")
        f.write("- **k=1**: Returns the single most similar chunk. Fast, minimal context.\n")
        f.write("- **k=3**: Returns top 3 chunks. Balances context size and noise.\n")
        f.write("- **k=5**: Returns top 5 chunks. More context, but may include less relevant chunks.\n\n")

        f.write("### Trade-offs\n\n")
        f.write("- **Context Size**: Higher k provides more context for LLM generation\n")
        f.write("- **Recall**: Higher k increases chance of finding relevant information\n")
        f.write("- **Noise**: Higher k may include less relevant chunks\n")
        f.write("- **Latency**: Higher k increases retrieval time (linear)\n")
        f.write("- **Cost**: Higher k increases LLM token consumption for context\n\n")

        f.write("### Why Query and Document Embeddings Must Use the Same Model\n\n")
        f.write("Embeddings from different models live in different semantic spaces.\n")
        f.write("Using the same model ensures that query and document embeddings are comparable,\n")
        f.write("allowing meaningful similarity calculations. Different models would produce\n")
        f.write("incompatible vector spaces, making similarity scores meaningless.\n\n")

    print()
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
