# Similarity Search and Top-K Retrieval Results

## Configuration

**Sample Query:** How can a learner reset their password?
**Database path:** data/chroma_db
**Collection name:** healthcompass_documents
**Embedding dimension:** 1536
**Embedding model:** text-embedding-3-small

**Note:** API key not configured. Results are mock data for demonstration purposes.

## Collection Information

**Name:** healthcompass_documents
**Record count:** 1
**Vector dimension:** 1536
**Metadata:** {'hnsw:M': 16, 'hnsw:construction_ef': 200, 'hnsw:space': 'cosine'}

## Distance Score Explanation

The results use **cosine distance** as the similarity metric.

- **Lower distance values** indicate higher similarity (closer in semantic space)
- Distance range: 0.0 (identical) to 2.0 (opposite) for normalized vectors
- A distance of 0.0 means the query and chunk are semantically identical
- A distance around 0.3-0.5 typically indicates strong semantic similarity

## Retrieval Results by k Value

### k=1

**Number of results returned:** 1

#### Rank 1

**Distance:** 0.1000
**Chunk ID:** chunk_0
**Source:** test_guidance.txt
**Filename:** test_guidance.txt
**Chunk Index:** 0
**Section:** Introduction
**Page Number:** 1
**Document Type:** guidance
**Text:** Document chunk 0 - This is a test vaccination guidance document for HealthCompass public health response.

### k=3

**Number of results returned:** 1

#### Rank 1

**Distance:** 0.1000
**Chunk ID:** chunk_0
**Source:** test_guidance.txt
**Filename:** test_guidance.txt
**Chunk Index:** 0
**Section:** Introduction
**Page Number:** 1
**Document Type:** guidance
**Text:** Document chunk 0 - This is a test vaccination guidance document for HealthCompass public health response.

### k=5

**Number of results returned:** 1

#### Rank 1

**Distance:** 0.1000
**Chunk ID:** chunk_0
**Source:** test_guidance.txt
**Filename:** test_guidance.txt
**Chunk Index:** 0
**Section:** Introduction
**Page Number:** 1
**Document Type:** guidance
**Text:** Document chunk 0 - This is a test vaccination guidance document for HealthCompass public health response.

## Analysis

### Effect of k on Results

- **k=1**: Returns the single most similar chunk. Fast, minimal context.
- **k=3**: Returns top 3 chunks. Balances context size and noise.
- **k=5**: Returns top 5 chunks. More context, but may include less relevant chunks.

### Trade-offs

- **Context Size**: Higher k provides more context for LLM generation
- **Recall**: Higher k increases chance of finding relevant information
- **Noise**: Higher k may include less relevant chunks
- **Latency**: Higher k increases retrieval time (linear)
- **Cost**: Higher k increases LLM token consumption for context

### Why Query and Document Embeddings Must Use the Same Model

Embeddings from different models live in different semantic spaces.
Using the same model ensures that query and document embeddings are comparable,
allowing meaningful similarity calculations. Different models would produce
incompatible vector spaces, making similarity scores meaningless.

