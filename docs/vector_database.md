# Vector Database for HealthCompass

## Overview

HealthCompass uses ChromaDB as a vector database to store document embeddings alongside their source text and metadata. This enables efficient semantic search and retrieval for the RAG (Retrieval-Augmented Generation) system.

## Why Use a Vector Database?

A vector database is specifically designed to store and query high-dimensional vectors (embeddings) efficiently. Unlike traditional databases that are optimized for exact matches on structured data, vector databases use approximate nearest neighbor (ANN) algorithms to find similar vectors based on semantic similarity.

**Key advantages:**
- **Semantic Search**: Find documents similar in meaning, not just keyword matches
- **Scalability**: Efficiently handle millions of vectors with fast similarity search
- **Integration**: Seamlessly works with embedding models for RAG applications
- **Metadata Support**: Store rich metadata alongside vectors for filtering and context

## Vector Dimension and Model Compatibility

The vector dimension of the collection must match the embedding model used to generate the vectors. Different embedding models produce vectors of different dimensions:

| Model | Dimension |
|-------|-----------|
| text-embedding-3-small | 1536 |
| text-embedding-3-large | 3072 |
| text-embedding-ada-002 | 1536 |

The vector store automatically configures the correct dimension based on the `EMBEDDING_MODEL` environment variable. If you change the embedding model, you must either recreate the collection or ensure all existing embeddings use the same dimension.

## Record Schema

Each record in the vector database contains:

- **id**: Unique identifier for the record (typically derived from chunk ID)
- **embedding**: The high-dimensional vector representing the text
- **text**: The original source text for the chunk
- **metadata**: Rich metadata including:
  - `source`: Original document source
  - `filename`: Document filename
  - `chunk_id`: Chunk identifier
  - `section`: Document section (if available)
  - `page_number`: Page number (if available)
  - `document_type`: Type of document (guidance, clinical, etc.)

### Example Record

```python
{
    "id": "test_record_001",
    "embedding": [0.1, 0.2, 0.3, ...],  # 1536 dimensions for text-embedding-3-small
    "text": "This is a test vaccination guidance document.",
    "metadata": {
        "source": "guidance.txt",
        "filename": "guidance.txt",
        "chunk_id": "0",
        "section": "Introduction",
        "page_number": "1",
        "document_type": "guidance"
    }
}
```

## Why Store Text and Metadata with Vectors?

Storing the original text and metadata alongside vectors is crucial for:

1. **Citation**: Accurately cite sources when generating answers
2. **Context**: Provide full context when retrieving similar documents
3. **Verification**: Ensure retrieved content matches user queries
4. **Filtering**: Filter results by metadata (e.g., specific documents, sections)
5. **Debugging**: Trace retrieval results back to source documents

Without stored text and metadata, you would only have similarity scores without knowing what documents were matched.

## Configuration

### Environment Variables

Configure the vector database using environment variables:

```bash
# Database storage path (default: data/chroma_db)
CHROMA_DB_PATH=data/chroma_db

# Collection name (default: healthcompass_documents)
CHROMA_COLLECTION_NAME=healthcompass_documents

# Embedding model (determines vector dimension)
EMBEDDING_MODEL=text-embedding-3-small
```

### Example .env Configuration

```bash
# Vector Database Configuration
CHROMA_DB_PATH=data/chroma_db
CHROMA_COLLECTION_NAME=healthcompass_documents
EMBEDDING_MODEL=text-embedding-3-small
```

## Installation

ChromaDB is already included in the project dependencies:

```bash
pip install -e .
```

Or install the specific dependency:

```bash
pip install chromadb>=0.4.0,<1.0
```

## Usage

### Initialize Vector Database

```python
from healthcompass.vector_store import initialize_vector_store, get_vector_store_config

# Get configuration from environment variables
config = get_vector_store_config()

# Initialize database (creates directory and collection if needed)
collection = initialize_vector_store(config)
```

### Insert a Record

```python
from healthcompass.vector_store import VectorRecord, insert_record

record = VectorRecord(
    id="chunk_001",
    embedding=[0.1, 0.2, 0.3, ...],  # Your embedding vector
    text="Vaccination guidance text...",
    metadata={
        "source": "guidance.txt",
        "filename": "guidance.txt",
        "chunk_id": "0",
        "section": "Introduction",
        "page_number": "1",
        "document_type": "guidance"
    }
)

insert_record(collection, record)
```

### Retrieve a Record

```python
from healthcompass.vector_store import get_record

retrieved = get_record(collection, "chunk_001")
if retrieved:
    print(f"Text: {retrieved.text}")
    print(f"Metadata: {retrieved.metadata}")
    print(f"Vector length: {len(retrieved.embedding)}")
```

### Health Check

```python
from healthcompass.vector_store import health_check

if health_check():
    print("Vector database is accessible and healthy")
else:
    print("Vector database health check failed")
```

## Running Tests

### Unit Tests

Run the vector database test suite:

```bash
pytest tests/test_vector_database.py -v
```

The tests use temporary databases and deterministic test vectors, so they don't require API keys or paid services.

### Integration Test

Run the insert and readback test script:

```bash
python experiments/vector_db_readback.py
```

This script:
1. Initializes the vector database
2. Creates a test record with a deterministic embedding
3. Inserts the record
4. Reads it back
5. Verifies ID, vector length, text, and metadata match
6. Generates a report in `experiments/outputs/vector_db_readback.md`

## How to Run the Database Setup

### Step 1: Configure Environment

Create or update your `.env` file:

```bash
CHROMA_DB_PATH=data/chroma_db
CHROMA_COLLECTION_NAME=healthcompass_documents
EMBEDDING_MODEL=text-embedding-3-small
```

### Step 2: Run Health Check

```bash
python -c "from healthcompass.vector_store import health_check; health_check()"
```

### Step 3: Run Insert/Readback Test

```bash
python experiments/vector_db_readback.py
```

### Step 4: Verify Output

Check the generated report:

```bash
cat experiments/outputs/vector_db_readback.md
```

## Troubleshooting

### Dimension Mismatch Error

If you see "Collection dimension mismatch", it means the existing collection has a different vector dimension than the configured embedding model. Options:

1. **Delete and recreate the collection** (WARNING: This deletes all data):
   ```bash
   rm -rf data/chroma_db
   ```

2. **Use the same embedding model** that was used to create the collection

3. **Create a new collection** with a different name

### Permission Errors

If you encounter permission errors accessing the database path:

```bash
# On Linux/Mac
chmod +w data/chroma_db

# On Windows
# Ensure the directory is not read-only in file properties
```

### Collection Already Exists

The vector store automatically loads existing collections instead of creating new ones. This prevents accidental data loss. To start fresh, delete the database directory or use a different collection name.

## Performance Considerations

### Batching

When inserting large numbers of records, use batch operations:

```python
# ChromaDB supports batch insertion
collection.add(
    ids=[r.id for r in records],
    embeddings=[r.embedding for r in records],
    documents=[r.text for r in records],
    metadatas=[r.metadata for r in records]
)
```

### Storage Requirements

Each 1536-dimensional vector (float32) requires approximately 6KB of storage. Plan storage accordingly:
- 1,000 documents: ~6MB
- 10,000 documents: ~60MB
- 100,000 documents: ~600MB

### Index Configuration

The collection uses HNSW (Hierarchical Navigable Small World) indexing with:
- `hnsw:space`: cosine similarity
- `hnsw:construction_ef`: 200 (index construction accuracy)
- `hnsw:M`: 16 (connectivity parameter)

These parameters balance build time, memory usage, and query accuracy.

## Security Notes

- **Never commit `.env` files** to version control
- **Never commit database directories** containing sensitive data
- **Use appropriate file permissions** on the database directory
- **Consider encryption** for production deployments with sensitive data

## Future Enhancements

Planned improvements to the vector database integration:

- **Semantic Search**: Add similarity search functionality
- **Filtering**: Support metadata-based filtering
- **Batch Operations**: Optimized bulk insert and query operations
- **Index Tuning**: Configurable index parameters for different use cases
- **Backup/Restore**: Database backup and restore functionality
