# Embeddings for HealthCompass RAG

## What are embeddings?

Embeddings are numerical vector representations of text that capture semantic meaning. Instead of matching keywords, embeddings allow systems to find text that is similar in meaning, even when different words are used. For HealthCompass, this enables finding relevant public-health guidance based on the meaning of user questions, not just exact word matches.

## How the API is called

The embedding generation uses the OpenAI Python SDK to call OpenAI-compatible embedding APIs:

1. Text chunks are prepared from the document chunking pipeline
2. Chunks are batched to reduce API overhead
3. Each batch is sent to the embeddings API with the configured model
4. The API returns embedding vectors for each chunk
5. Vectors are matched back to their source chunks and stored together

## Which model is used

The default model is `text-embedding-3-small`, OpenAI's efficient embedding model. This can be configured via the `EMBEDDING_MODEL` environment variable. The model provides a good balance of:
- Semantic quality for public-health text
- Computational efficiency
- Cost-effectiveness for large document collections

## Why the model is configured through environment variables

Using environment variables for model configuration provides:

- **Security**: API keys are never hardcoded in source code
- **Flexibility**: Different environments can use different models/providers
- **Consistency**: Same model can be used across development, testing, and production
- **Easy switching**: Model changes don't require code deployment
- **Reproducibility**: Model name is stored in the manifest for each embedding set

## Why document chunks and queries must use the same embedding model

Embeddings are model-specific - different models produce vectors in different semantic spaces. Using the same model for both document chunks and user queries ensures:

- **Semantic compatibility**: Vectors are in the same mathematical space
- **Accurate similarity**: Similarity calculations are meaningful
- **Consistent results**: Same query produces consistent retrieval
- **Fair comparison**: All content is evaluated on the same basis

Mixing models would produce incomparable vectors and unreliable retrieval results.

## How source text and metadata are stored with vectors

Each embedded chunk stores:

```python
{
    "text": "Original chunk text...",
    "source": "guideline.pdf",
    "filename": "guideline.pdf",
    "chunk_id": 0,
    "metadata": {
        "section": "Vaccination",
        "version": "1.0",
        "region": "District A"
    },
    "embedding": [0.0123, -0.0456, ...],
    "embedding_model": "text-embedding-3-small"
}
```

This structure ensures:
- **Citation**: Original text can be displayed to users
- **Traceability**: Source document and position are preserved
- **Context**: Metadata provides additional filtering and context
- **Reproducibility**: Model name allows future regeneration

## What vector dimension represents

Vector dimension is the number of numerical values in each embedding vector. For `text-embedding-3-small`, this is 1536 dimensions. Each dimension captures different aspects of semantic meaning:

- Higher dimensions can represent more nuanced semantic relationships
- Dimensionality is determined by the model, not configurable
- All vectors from the same model have the same dimension
- Dimension affects storage size and computation cost

## How batching reduces repeated API calls

Batching processes multiple text chunks in a single API request:

- **Without batching**: 100 chunks = 100 API calls
- **With batching (batch_size=100)**: 100 chunks = 1 API call

Benefits:
- Reduced API overhead and latency
- Lower total cost (many providers charge per request)
- Faster processing for large document collections
- Better utilization of network bandwidth

Trade-offs:
- Larger batches increase per-request complexity
- Failed batches require retrying more chunks
- Memory usage increases with batch size

## How cost and latency increase as corpus size grows

**Cost factors:**
- API calls scale with number of chunks (reduced by batching)
- Storage scales with chunk count × vector dimension
- Vector dimension affects both storage and computation
- Different pricing models across providers

**Latency factors:**
- API call time increases with batch size
- Network latency for each API request
- Processing time for vector operations
- Indexing time grows with corpus size

**Scaling strategies:**
- Use appropriate batch sizes for your corpus
- Consider incremental embedding for growing collections
- Cache embeddings for frequently accessed documents
- Monitor costs and optimize batch sizes accordingly

## How to run the script

### Prerequisites

1. Configure your API key in `.env` file:
   ```env
   OPENAI_API_KEY=your_api_key_here
   EMBEDDING_MODEL=text-embedding-3-small
   OPENAI_BASE_URL=https://api.openai.com/v1
   EMBEDDING_BATCH_SIZE=64
   MAX_RETRY_ATTEMPTS=3
   ```

2. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Run embedding generation

```bash
python experiments/embeddings/generate_embeddings.py
```

### Expected output

The script will:
1. Create a sample corpus from vaccination guidance text
2. Generate embeddings using the configured API
3. Validate the results
4. Save embedded chunks to `experiments/outputs/embedded_chunks.json`
5. Generate a human-readable report at `experiments/outputs/embedding_sample.md`
6. Display a comprehensive run summary

### Sample output

```
======================================================================
HealthCompass Embedding Generation
======================================================================

Creating sample corpus from vaccination guidance...
Created 3 chunks for embedding

Generating embeddings via API...
Total chunks: 3
Skipped existing embeddings: 0
Chunks to process: 3
Saved progress after batch 1/1

[OK] Successfully generated 3 embeddings
   Model: text-embedding-3-small
   Vector dimension: 1536

======================================================================
RUN SUMMARY
======================================================================
Total chunks: 3
Skipped existing embeddings: 0
Chunks processed: 3
Successfully embedded: 3
Failed chunks: 0
Total batches: 1
Input token count (estimated): 900
Estimated cost: $0.000018
Batch size: 10
Retry attempts: 0

[OK] Validation passed

Sample chunk:
  Source: vaccination_guidance_sample.txt
  Chunk ID: 0
  Text: Vaccination Guidelines for Public Health Response...
  Vector length: 1536
  Sample values: [0.0123, -0.0456, 0.0789]

Saved embedded chunks to: experiments/outputs/embedded_chunks.json
Saved sample report to: experiments/outputs/embedding_sample.md
```

## Batch Embedding Management

### Batch size configuration

- Configurable via `EMBEDDING_BATCH_SIZE` environment variable (default: 64)
- Larger batches reduce API overhead but increase memory usage
- Smaller batches provide better error isolation but increase API calls
- Choose based on your corpus size and API rate limits

### Skip existing embeddings

- Uses content-based chunk IDs to identify already-embedded chunks
- Automatically skips chunks that already have embeddings in the output file
- Reduces unnecessary API calls and costs for re-runs
- Enables efficient incremental processing of growing corpora

### Retry with exponential backoff

- Automatic retry for temporary API failures (rate limits, timeouts, connection errors)
- Exponential backoff sequence: 1, 2, 4, 8 seconds between attempts
- Configurable maximum retry attempts via `MAX_RETRY_ATTEMPTS` (default: 3)
- Does not retry permanent configuration errors (missing API keys, etc.)
- Failed batches are recorded in the run summary for troubleshooting

### Progress saving and resumability

- Embeddings are saved incrementally after each successful batch
- Uses atomic file operations to prevent data corruption
- If the process stops, it can continue from where it left off
- Existing embeddings are never deleted during re-runs
- Enables processing of large corpora without risking complete data loss

### Run summary

The embedding generation provides a comprehensive summary:
- Total chunks processed
- Number of skipped existing embeddings
- Successfully embedded chunks
- Failed chunks and batch indices
- Total batches processed
- Estimated input token count
- Approximate cost in USD
- Batch size and retry attempts

### Cost estimation

- Estimates cost based on token count and model pricing
- Uses approximate pricing: $0.02 per 1M tokens for text-embedding-3-small
- Clearly labeled as estimated cost (actual cost may vary)
- Helps budget and plan large corpus processing
- Token count is estimated from character count (~4 chars per token)

## Testing

Run the embedding tests with mocked API responses:

```bash
pytest tests/test_embeddings.py -v
```

Tests cover:
- Configuration retrieval and validation
- Chunk preparation from different formats
- Successful embedding generation
- Batch processing with configurable batch size
- Error handling and retry logic
- Metadata preservation
- Validation logic
- Security (no secrets in logs, metadata isolation)
- Chunk ID generation for deduplication
- Loading and skipping existing embeddings
- Cost estimation
- Exponential backoff without real API calls
- Run summary calculations
- Batch splitting logic

## Integration with HealthCompass RAG

The embedding pipeline integrates with existing HealthCompass components:

1. **Document loading**: Multi-format document ingestion
2. **Text cleaning**: Normalized text preparation
3. **Chunking**: Token-aware chunking with overlap
4. **Embeddings**: Vector generation (this module)
5. **Vector search**: Future work
6. **RAG retrieval**: Future work

This modular design allows each component to be developed and tested independently while maintaining clean interfaces between stages.
