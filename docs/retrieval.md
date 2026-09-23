# Similarity Search and Top-K Retrieval

## Overview

HealthCompass uses semantic similarity search to retrieve the most relevant document chunks for a user query. The retrieval pipeline converts natural language queries into embeddings, searches the vector database for semantically similar chunks, and returns ranked results with similarity scores.

## Complete Retrieval Process

The retrieval process follows this pipeline:

```
User Query → Query Embedding → Vector Search → Ranked Chunks
```

### Step 1: User Query
The user provides a natural language question, such as:
- "How can a learner reset their password?"
- "What are the vaccination requirements for healthcare workers?"
- "What are the symptoms of influenza?"

### Step 2: Query Embedding
The query is converted to a numerical vector using the same embedding model used for document chunks:

```python
from healthcompass.vector_store import embed_query

query_embedding = embed_query("How can a learner reset their password?")
```

**Key requirement**: The query and document embeddings must use the same model. Different models produce vectors in different semantic spaces, making similarity calculations meaningless.

### Step 3: Vector Search
The query embedding is compared against all document embeddings in the vector database using cosine similarity:

```python
from healthcompass.vector_store import retrieve, initialize_vector_store

collection = initialize_vector_store()
results = retrieve(
    query="How can a learner reset their password?",
    collection=collection,
    k=3
)
```

### Step 4: Ranked Chunks
The system returns the top-k most similar chunks, ranked by semantic similarity with distance scores.

## What is Top-K?

Top-k retrieval returns the k most similar document chunks for a given query, where:

- **k** is the number of results to return (e.g., k=3 returns top 3 results)
- Results are ranked by similarity (lower distance = higher similarity)
- Only the most relevant chunks are included in the response

## How k Affects Retrieval

### Context Size
- **Higher k**: Provides more context for LLM generation, improving answer quality
- **Lower k**: Reduces context size, may miss relevant information

### Recall
- **Higher k**: Increases chance of finding all relevant information
- **Lower k**: May miss important but less semantically similar chunks

### Noise
- **Higher k**: May include less relevant chunks, adding noise to the context
- **Lower k**: Focuses on the most relevant chunks, reducing noise

### Latency
- **Higher k**: Increases retrieval time (linear growth with k)
- **Lower k**: Faster retrieval, better for real-time applications

### Cost
- **Higher k**: Increases LLM token consumption for context processing
- **Lower k**: Reduces computational cost for LLM generation

### Recommended k Values
- **k=1**: Quick answers, minimal context
- **k=3**: Balanced approach (default)
- **k=5**: Comprehensive answers, more context
- **k=10**: Complex queries requiring extensive context

## Distance Score Explanation

HealthCompass uses **cosine distance** as the similarity metric:

- **Range**: 0.0 to 2.0 for normalized vectors
- **Lower values** indicate higher similarity (closer in semantic space)
- **0.0**: Identical vectors (perfect semantic match)
- **~0.3-0.5**: Strong semantic similarity
- **~0.5-0.7**: Moderate semantic similarity
- **>1.0**: Low similarity or unrelated content

**Important**: Lower distance = higher similarity. This is different from similarity scores where higher = better.

## Retrieved Result Schema

Each retrieved result includes:

```python
@dataclass
class RetrievalResult:
    rank: int              # 1 for most similar, 2 for second, etc.
    chunk_id: str         # Unique identifier for the chunk
    distance: float        # Cosine distance (lower = more similar)
    text: str             # Original chunk text
    metadata: dict        # Source information and chunk details
```

### Metadata Fields
- **source**: Original document source
- **filename**: Document filename
- **chunk_id**: Chunk index within document
- **section**: Document section (if available)
- **page_number**: Page number (if available)
- **document_type**: Type of document (guidance, clinical, etc.)

## Usage Examples

### Basic Retrieval

```python
from healthcompass.vector_store import retrieve, initialize_vector_store

# Initialize database
collection = initialize_vector_store()

# Retrieve top 3 results
results = retrieve(
    query="How can a learner reset their password?",
    collection=collection,
    k=3
)

# Display results
for result in results:
    print(f"Rank: {result.rank}")
    print(f"Distance: {result.distance:.4f}")
    print(f"Text: {result.text}")
    print(f"Source: {result.metadata.get('source', 'N/A')}")
```

### Custom k Value

```python
# Retrieve top 5 results
results = retrieve(
    query="What are the vaccination requirements?",
    collection=collection,
    k=5
)
```

### Custom Embedding Model

```python
# Use a different embedding model
results = retrieve(
    query="Query text",
    collection=collection,
    k=3,
    embedding_model="text-embedding-3-large"
)
```

## Running the Retrieval Demo

### Prerequisites
1. Vector database must be initialized with documents
2. Documents must be embedded and stored in the collection
3. OpenAI API key must be configured for query embedding

### Step 1: Initialize Vector Database

```bash
python experiments/vector_db_readback.py
```

This creates the collection and inserts test records.

### Step 2: Run Retrieval Demo

```bash
python experiments/retrieval_demo.py
```

This demonstrates retrieval with different k values (1, 3, 5) and generates a report.

### Step 3: View Results

```bash
cat experiments/outputs/retrieval_results.md
```

## Error Handling

### Missing API Key
```python
VectorStoreError: OPENAI_API_KEY environment variable is not set.
```
**Solution**: Configure OPENAI_API_KEY in .env file or environment variables.

### Empty Collection
```python
VectorStoreError: Cannot retrieve from empty collection.
```
**Solution**: Insert documents using the vector_db_readback.py script first.

### Invalid k Value
```python
VectorStoreError: Invalid k value: 0. k must be greater than 0.
```
**Solution**: Use a positive integer for k (e.g., k=1, k=3, k=5).

### Dimension Mismatch
```python
VectorStoreError: Collection dimension mismatch: expected 1536, found 3072.
```
**Solution**: Ensure query and document embeddings use the same model.

## Configuration

### Environment Variables

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Model Configuration
EMBEDDING_MODEL=text-embedding-3-small

# Vector Database Configuration
CHROMA_DB_PATH=data/chroma_db
CHROMA_COLLECTION_NAME=healthcompass_documents
```

## Testing

Run the retrieval test suite:

```bash
pytest tests/test_vector_database.py -k "retrieve or embed" -v
```

Tests cover:
- Query embedding uses configured model
- Query vector dimension validation
- Retrieval returns requested number of results
- Retrieval includes IDs, scores, text, and metadata
- Different k values return different result counts
- Empty collection handling
- Invalid k value rejection
- API calls are mocked (no paid API required)

## Why Query and Document Embeddings Must Use the Same Model

Embeddings from different models live in different semantic spaces. Using the same model ensures:

1. **Comparable Vectors**: Query and document embeddings exist in the same semantic space
2. **Meaningful Similarity**: Distance scores accurately reflect semantic similarity
3. **Consistent Results**: Retrieval behavior is predictable and reproducible

**Example**: If documents are embedded with `text-embedding-3-small` (1536 dimensions) but queries use `text-embedding-3-large` (3072 dimensions), the vectors are incompatible and similarity calculations are meaningless.

## Performance Considerations

### Retrieval Latency
- **Vector search**: Typically 10-100ms for k=3-10
- **Query embedding**: ~50-200ms depending on model
- **Total**: ~100-300ms per query

### Storage Requirements
- Each embedding: ~6KB (1536 dimensions × 4 bytes)
- 1,000 documents: ~6MB
- 10,000 documents: ~60MB

### Scalability
- ChromaDB handles millions of vectors efficiently
- HNSW indexing provides O(log n) search complexity
- Retrieval time grows logarithmically with collection size

## Integration with RAG Pipeline

The retrieval results are designed for integration with RAG generation:

1. **Retrieval**: Get top-k relevant chunks
2. **Context Construction**: Format chunks for LLM context
3. **Generation**: Use LLM to generate grounded answers
4. **Citation**: Use chunk metadata for source attribution

Example context construction:

```python
context = "\n\n".join([
    f"Source: {r.metadata.get('source', 'N/A')}\n"
    f"Text: {r.text}"
    for r in results
])
```

## Troubleshooting

### No Results Returned
- Check if collection has documents: `collection.count()`
- Verify query is relevant to available documents
- Try increasing k value

### Poor Quality Results
- Check embedding model consistency
- Verify document quality and chunking
- Try different query phrasing
- Consider increasing k for more context

### API Errors
- Verify OPENAI_API_KEY is configured
- Check API rate limits
- Ensure internet connectivity for API calls

## Future Enhancements

Planned improvements to the retrieval system:

- **Hybrid Search**: Combine semantic search with keyword matching
- **Reranking**: Apply cross-encoder reranking for better relevance
- **Metadata Filtering**: Filter results by document type, date, etc.
- **Query Expansion**: Automatically expand queries for better recall
- **Caching**: Cache query embeddings for repeated queries
- **Batch Retrieval**: Support multiple queries in a single request
