# Retrieval Evaluation

This document explains the retrieval evaluation system for HealthCompass, which uses Recall@k and Precision@k metrics to measure retrieval quality.

## Overview

The evaluation system measures how well the vector retriever finds relevant document chunks for user queries. It uses a labelled query set with known relevant chunks to calculate standard information retrieval metrics.

## Metrics

### Recall@k

**Recall@k** measures the fraction of relevant chunks that are retrieved in the top-k results.

```
Recall@k = (number of relevant chunks retrieved in top-k) / (total number of relevant chunks)
```

**Example:**
- A query has 2 relevant chunks
- Top-5 retrieval returns 1 of them
- Recall@5 = 1/2 = 0.50 (50%)

**Why Recall@k matters:**
- High recall means the retriever is finding most/all relevant information
- Low recall means important chunks are being missed
- For RAG systems, low recall can lead to incomplete or inaccurate answers
- Recall is critical when missing information could have serious consequences (e.g., public health guidance)

### Precision@k

**Precision@k** measures the fraction of retrieved chunks that are actually relevant.

```
Precision@k = (number of relevant chunks retrieved in top-k) / (number of chunks retrieved in top-k)
```

**Example:**
- Top-5 retrieval returns 5 chunks
- 2 of them are labelled relevant
- Precision@5 = 2/5 = 0.40 (40%)

**Why Precision@k matters:**
- High precision means most retrieved chunks are useful
- Low precision means the retriever is returning irrelevant content
- For RAG systems, low precision wastes context window and may introduce noise
- Precision affects the quality and relevance of generated answers

### Recall vs Precision

- **Recall**: "Of all the relevant chunks, how many did we find?"
- **Precision**: "Of the chunks we retrieved, how many are actually relevant?"

In RAG systems:
- **High recall** ensures the LLM has access to all relevant information
- **High precision** ensures the LLM isn't distracted by irrelevant content
- The ideal retriever achieves both high recall and high precision
- There's often a trade-off: increasing k (retrieving more chunks) typically increases recall but may decrease precision

## Labelled Query Set

The evaluation uses a manually labelled query set based on the actual documents stored in the vector database.

### Creation Process

1. **Inspect stored chunks**: All chunks in the vector database were examined to understand their content
2. **Create realistic queries**: 8 realistic public-health queries were written based on the actual chunk content
3. **Label relevant chunks**: For each query, the chunk IDs that contain relevant information were identified
4. **Document rationale**: Each query includes an explanation of why the labelled chunks are relevant

### Query Set Statistics

- **Number of queries**: 8
- **Source document**: `vaccination_guidance.txt`
- **Chunks in database**: 2 (`vaccination_chunk_0`, `vaccination_chunk_1`)
- **Topics covered**: Priority groups, storage and handling, core principles, dosing and administration, monitoring and surveillance, adverse events, cold chain protocols, inventory management

### Example Query

```json
{
  "query": "What are the priority groups for vaccination?",
  "relevant_chunk_ids": ["vaccination_chunk_0"],
  "relevant_source": "vaccination_guidance.txt",
  "explanation": "Section 2: Priority Groups is covered in chunk 0",
  "expected_topic": "priority groups"
}
```

### Multiple Relevant Chunks

Some queries have multiple relevant chunks because:
- Information spans multiple chunks (e.g., "adverse event monitoring" appears in both chunks)
- The topic is covered across chunk boundaries
- Multiple sections contain relevant information

Example:
```json
{
  "query": "How should vaccines be stored and handled?",
  "relevant_chunk_ids": ["vaccination_chunk_0", "vaccination_chunk_1"],
  "explanation": "Section 4: Storage and Handling spans both chunks 0 and 1"
}
```

## Running the Evaluation

### Prerequisites

1. Vector database must be populated with chunks
2. `OPENAI_API_KEY` must be set in environment (for query embedding)
3. ChromaDB collection must exist at the configured path

### Run the Evaluation

```bash
# From repository root
python -m evaluation.run_evaluation
```

### Output

The evaluation generates two files in `evaluation/results/`:

1. **`retrieval_evaluation.json`**: Machine-readable results with all query details
2. **`retrieval_evaluation_report.md`**: Human-readable report with metrics and failure analysis

## Evaluation Results

### Metrics

The evaluation calculates aggregate metrics across all queries at different k values:

| Metric | Description |
|---|---|
| Recall@1 | Fraction of relevant chunks found in the top-1 result |
| Recall@3 | Fraction of relevant chunks found in the top-3 results |
| Recall@5 | Fraction of relevant chunks found in the top-5 results |
| Precision@1 | Fraction of top-1 results that are relevant |
| Precision@3 | Fraction of top-3 results that are relevant |
| Precision@5 | Fraction of top-5 results that are relevant |

### Per-Query Results

For each query and each k value, the report shows:
- Query text
- Relevant chunk IDs
- Retrieved chunks with relevance status
- Distance scores
- Recall@k and Precision@k values

### Failure Analysis

Queries with Recall@k < 100% are analyzed with:
- Expected relevant chunks
- Actually retrieved chunks
- Observed evidence
- Likely cause of failure
- Possible improvements

## Current Results

### Measured Performance

Run the evaluation to see the current metrics:

```bash
python -m evaluation.run_evaluation
```

The actual results will be saved to `evaluation/results/retrieval_evaluation_report.md`.

### Common Failure Patterns

Based on the evaluation results, common retrieval failures may include:

1. **Chunk boundary issues**: Information split across multiple chunks
2. **Query wording mismatch**: Query uses different terminology than source
3. **Insufficient k**: Too few chunks retrieved to find all relevant information
4. **Semantic similarity weakness**: Embedding doesn't capture the relationship
5. **Metadata filtering**: Relevant chunks filtered out by metadata constraints

## Improving Recall

Based on failure analysis, potential improvements include:

### Chunking Strategy
- **Smaller chunks**: Reduces chance of splitting relevant information
- **Larger chunks**: Increases context per chunk, may improve semantic match
- **Sentence boundaries**: Split at natural sentence boundaries
- **Semantic chunking**: Use semantic similarity to identify natural break points

### Retrieval Parameters
- **Increase k**: Retrieve more chunks to find more relevant information
- **Hybrid search**: Combine semantic search with keyword search
- **Reranking**: Re-rank retrieved results using a more sophisticated model
- **Query expansion**: Expand query with related terms or synonyms

### Query Processing
- **Query rewriting**: Rewrite queries to match source terminology
- **Multiple queries**: Generate multiple query variants and merge results
- **Query augmentation**: Add context or domain-specific terms to queries

### Embedding Model
- **Different model**: Try a different embedding model (e.g., `text-embedding-3-large`)
- **Fine-tuning**: Fine-tune embeddings on domain-specific data
- **Domain adaptation**: Use embeddings trained on medical/public health text

## Testing

Unit tests for the evaluation metrics are in `tests/test_retrieval_evaluation.py`:

```bash
python -m pytest tests/test_retrieval_evaluation.py
```

Tests cover:
- Recall@k calculation (perfect, partial, zero recall)
- Precision@k calculation (perfect, partial, zero precision)
- Multiple relevant chunks
- Edge cases (empty results, k larger than available, duplicates)
- Dataclass validation

## References

- Information Retrieval: [Recall and Precision](https://en.wikipedia.org/wiki/Precision_and_recall)
- RAG Evaluation: [Evaluating Retrieval-Augmented Generation](https://arxiv.org/abs/2301.06824)
