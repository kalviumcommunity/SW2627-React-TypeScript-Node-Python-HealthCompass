"""Vector database insertion and readback test for HealthCompass."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from healthcompass.vector_store import (
    VectorRecord,
    get_collection_info,
    get_record,
    get_vector_store_config,
    health_check,
    initialize_vector_store,
    insert_record,
)


def create_test_embedding(dimension: int) -> list[float]:
    """Create a test embedding vector with the specified dimension.

    Args:
        dimension: The dimension of the embedding vector

    Returns:
        List of float values representing the embedding
    """
    # Create a simple test embedding with predictable values
    return [0.1 * (i + 1) for i in range(dimension)]


def main():
    """Main entry point for vector database readback test."""
    print("=" * 70)
    print("HealthCompass Vector Database Readback Test")
    print("=" * 70)
    print()

    # Get configuration
    print("Loading vector database configuration...")
    config = get_vector_store_config()
    print(f"Database path: {config.db_path}")
    print(f"Collection name: {config.collection_name}")
    print(f"Embedding dimension: {config.embedding_dimension}")
    print(f"Embedding model: {config.embedding_model}")
    print()

    # Perform health check
    print("Performing health check...")
    if not health_check(config):
        print("Health check failed. Exiting.")
        sys.exit(1)
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
    print(f"  Metadata: {info['metadata']}")
    print()

    # Create test record
    print("Creating test record...")
    test_id = "test_record_001"
    test_embedding = create_test_embedding(config.embedding_dimension)
    test_text = "This is a test vaccination guidance document for HealthCompass public health response."
    test_metadata = {
        "source": "test_guidance.txt",
        "filename": "test_guidance.txt",
        "chunk_id": "0",
        "section": "Introduction",
        "page_number": "1",
        "document_type": "guidance",
    }

    test_record = VectorRecord(
        id=test_id,
        embedding=test_embedding,
        text=test_text,
        metadata=test_metadata,
    )

    print(f"  Record ID: {test_record.id}")
    print(f"  Vector length: {len(test_record.embedding)}")
    print(f"  Text: {test_record.text}")
    print(f"  Metadata: {test_record.metadata}")
    print()

    # Insert test record
    print("Inserting test record...")
    try:
        inserted_id = insert_record(collection, test_record)
        print(f"Successfully inserted record with ID: {inserted_id}")
    except Exception as e:
        print(f"Failed to insert record: {e}")
        sys.exit(1)
    print()

    # Read back the record
    print("Reading back the record...")
    retrieved_record = get_record(collection, test_id)

    if retrieved_record is None:
        print("ERROR: Failed to retrieve the inserted record")
        sys.exit(1)

    print(f"Successfully retrieved record with ID: {retrieved_record.id}")
    print()

    # Verify the readback
    print("Verifying readback results:")
    print("-" * 70)

    # Verify ID
    id_match = retrieved_record.id == test_record.id
    print(f"ID match: {id_match}")
    if not id_match:
        print(f"  Expected: {test_record.id}")
        print(f"  Got: {retrieved_record.id}")

    # Verify vector length
    vector_length_match = len(retrieved_record.embedding) == len(test_record.embedding)
    print(f"Vector length match: {vector_length_match}")
    if not vector_length_match:
        print(f"  Expected: {len(test_record.embedding)}")
        print(f"  Got: {len(retrieved_record.embedding)}")

    # Verify text
    text_match = retrieved_record.text == test_record.text
    print(f"Text match: {text_match}")
    if not text_match:
        print(f"  Expected: {test_record.text}")
        print(f"  Got: {retrieved_record.text}")

    # Verify metadata
    metadata_match = retrieved_record.metadata == test_record.metadata
    print(f"Metadata match: {metadata_match}")
    if not metadata_match:
        print(f"  Expected: {test_record.metadata}")
        print(f"  Got: {retrieved_record.metadata}")

    print("-" * 70)

    # Overall verification
    all_match = id_match and vector_length_match and text_match and metadata_match
    if all_match:
        print()
        print("[SUCCESS] All verifications passed!")
        print()
        print("Final readback results:")
        print(f"  Record ID: {retrieved_record.id}")
        print(f"  Vector length: {len(retrieved_record.embedding)}")
        print(f"  Source text: {retrieved_record.text}")
        print(f"  Metadata: {retrieved_record.metadata}")
    else:
        print()
        print("[FAILED] Some verifications failed!")
        sys.exit(1)

    # Save output report
    output_dir = Path("experiments/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "vector_db_readback.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Vector Database Readback Test Results\n\n")
        f.write("## Configuration\n\n")
        f.write(f"**Database path:** {config.db_path}\n")
        f.write(f"**Collection name:** {config.collection_name}\n")
        f.write(f"**Embedding dimension:** {config.embedding_dimension}\n")
        f.write(f"**Embedding model:** {config.embedding_model}\n\n")

        f.write("## Collection Information\n\n")
        f.write(f"**Name:** {info['name']}\n")
        f.write(f"**Record count:** {info['count']}\n")
        f.write(f"**Vector dimension:** {info['dimension']}\n")
        f.write(f"**Metadata:** {info['metadata']}\n\n")

        f.write("## Test Record\n\n")
        f.write(f"**Record ID:** {test_record.id}\n")
        f.write(f"**Vector length:** {len(test_record.embedding)}\n")
        f.write(f"**Source text:** {test_record.text}\n")
        f.write(f"**Metadata:** {test_record.metadata}\n\n")

        f.write("## Readback Verification\n\n")
        f.write(f"**ID match:** {id_match}\n")
        f.write(f"**Vector length match:** {vector_length_match}\n")
        f.write(f"**Text match:** {text_match}\n")
        f.write(f"**Metadata match:** {metadata_match}\n\n")

        f.write("## Final Readback Results\n\n")
        f.write(f"**Record ID:** {retrieved_record.id}\n")
        f.write(f"**Vector length:** {len(retrieved_record.embedding)}\n")
        f.write(f"**Source text:** {retrieved_record.text}\n")
        f.write(f"**Metadata:** {retrieved_record.metadata}\n\n")

        f.write("## Conclusion\n\n")
        if all_match:
            f.write("The vector database is functioning correctly. ")
            f.write("The insert and readback test passed all verifications.")
        else:
            f.write("Some verifications failed. Please check the configuration.")

    print()
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
