# Retrieval Tuning Experiment

## Overview

This document describes a retrieval tuning experiment conducted to determine which retrieval settings return the most relevant chunks for the HealthCompass RAG system. The experiment compares multiple retrieval configurations, measures relevance using hit rates, and selects the best-performing configuration based on actual results.

## Why Retrieval Tuning is Necessary

Retrieval tuning is essential because:

1. **Different k values affect context size and noise**: Higher k provides more context but may include less relevant chunks, while lower k is focused but may miss important information.

2. **No universal optimal settings**: The best retrieval configuration depends on the specific document collection, query patterns, and use case.

3. **Performance trade-offs**: Context size, recall, noise, latency, and cost all vary with retrieval settings.

4. **Empirical validation**: Theoretical assumptions about optimal settings should be validated with actual retrieval results.

## Test Queries

The evaluation dataset contains 8 realistic queries based on the vaccination guidance document currently indexed in the HealthCompass vector database:

1. "What are the priority groups for vaccination?" → Expected: vaccination_guidance.txt (Section 2)
2. "How should vaccines be stored and handled?" → Expected: vaccination_guidance.txt (Section 4)
3. "What are the core vaccination principles?" → Expected: vaccination_guidance.txt (Section 1)
4. "How should dosing and administration be managed?" → Expected: vaccination_guidance.txt (Section 3)
5. "What monitoring and surveillance systems are needed?" → Expected: vaccination_guidance.txt (Section 5)
6. "Who should be prioritized for vaccination during emergencies?" → Expected: vaccination_guidance.txt (Section 2)
7. "What are the cold chain requirements for vaccines?" → Expected: vaccination_guidance.txt (Section 4)
8. "How should vaccine effectiveness be monitored?" → Expected: vaccination_guidance.txt (Section 5)

**Expected source methodology**: Each query is designed to match specific sections of the vaccination guidance document. The expected source is the document filename (`vaccination_guidance.txt`), and expected keywords help identify relevant sections when source matching alone is insufficient.

## Retrieval Settings Compared

The experiment compared two retrieval configurations:

### Configuration A
- **k = 3**
- **Score threshold**: None
- **Metadata filter**: None

### Configuration B
- **k = 5**
- **Score threshold**: None
- **Metadata filter**: None

These configurations were chosen to compare the effect of different k values on retrieval performance while keeping other settings constant.

## Relevance Measurement

### Top-1 Hit Rate

The top-1 hit rate measures whether the first retrieved result comes from the expected source:

```
top_1_hit_rate = top_1_hits / total_queries
```

**What it means**: Indicates how often the most similar chunk is from the expected document. Higher values suggest better ranking quality.

### Top-k Hit Rate

The top-k hit rate measures whether at least one of the retrieved results comes from the expected source:

```
top_k_hit_rate = queries_with_expected_source_in_results / total_queries
```

**What it means**: Indicates the recall capability of the retrieval system. Higher values suggest better ability to find relevant information anywhere in the top-k results.

### Additional Metrics

- **Average rank**: Average position of the expected source when retrieved (lower is better)
- **Queries with zero relevant**: Number of queries where no relevant chunk was found

## Actual Measured Results

The experiment was run with the vaccination guidance document containing 2 chunks and 8 test queries using mock retrieval results (deterministic embeddings for testing without API).

### Configuration Comparison

| Configuration | k | Top-1 Hit Rate | Top-k Hit Rate | Average Rank |
|---|---:|---:|---:|---:|
| Config A | 3 | 100.0% | 100.0% | 1.00 |
| Config B | 5 | 100.0% | 100.0% | 1.00 |

### Detailed Results

#### Config A (k=3)
- **Settings**: k=3, no score threshold, no metadata filter
- **Performance**:
  - Top-1 hits: 8/8
  - Top-k hits: 8/8
  - Top-1 hit rate: 100.0%
  - Top-k hit rate: 100.0%
  - Average rank: 1.00
  - Queries with zero relevant: 0

All 8 queries successfully retrieved the expected source document in the top result.

#### Config B (k=5)
- **Settings**: k=5, no score threshold, no metadata filter
- **Performance**:
  - Top-1 hits: 8/8
  - Top-k hits: 8/8
  - Top-1 hit rate: 100.0%
  - Top-k hit rate: 100.0%
  - Average rank: 1.00
  - Queries with zero relevant: 0

All 8 queries successfully retrieved the expected source document in the top result.

## Configuration Comparison

Both configurations achieved perfect performance on this small dataset:
- **Top-1 hit rate**: 100% for both configurations
- **Top-k hit rate**: 100% for both configurations
- **Average rank**: 1.00 for both configurations

## Selected Configuration

**Chosen configuration**: Config A

**Settings**:
- k = 3
- Score threshold = None
- Metadata filter = None

**Reason**: 
- Both configurations achieved identical performance (100% top-1 and top-k hit rates)
- When performance is equal, the smaller k value is preferred because it returns less unnecessary context
- k=3 provides a good balance between context size and noise while maintaining perfect recall on this dataset
- Smaller k reduces computational cost and LLM token consumption

## How to Run the Experiment

### Prerequisites
1. Vector database must be initialized with documents
2. Test queries file must exist at `evaluation/retrieval_queries.json`
3. For real API calls, OPENAI_API_KEY must be configured

### Step 1: Prepare Test Data

Ensure the vector database has indexed documents:

```bash
python experiments/vector_db_readback.py
```

### Step 2: Run Tuning Experiment

```bash
python evaluation/tune_retrieval.py
```

This will:
- Load test queries from `evaluation/retrieval_queries.json`
- Evaluate each configuration against all queries
- Calculate hit rates and aggregate results
- Select the best configuration
- Save results to `evaluation/results/`

### Step 3: View Results

```bash
# View detailed JSON results
cat evaluation/results/retrieval_tuning_results.json

# View summary JSON
cat evaluation/results/retrieval_tuning_summary.json

# View Markdown report
cat evaluation/results/retrieval_tuning_report.md
```

## Output Files

### Machine-Readable Results

- **retrieval_tuning_results.json**: Detailed results for every query and configuration
- **retrieval_tuning_summary.json**: Aggregated metrics for each configuration

### Human-Readable Report

- **retrieval_tuning_report.md**: Comprehensive report with configuration comparison, detailed results, and analysis

## Testing

Run the retrieval tuning test suite:

```bash
pytest tests/test_retrieval_tuning.py -v
```

Tests cover:
- Test queries load correctly
- Multiple retrieval configurations can be evaluated
- Top-1 hit calculation is correct
- Top-k hit calculation is correct
- Source matching works correctly
- Results are aggregated correctly
- Empty retrieval results are handled safely
- Invalid configuration values are rejected
- Best configuration selection logic

All tests use mocked retrieval results and do not require API calls.

## Limitations

This experiment has several important limitations:

1. **Small evaluation dataset**: Only 8 test queries on a single document type
2. **Single document collection**: Only vaccination guidance document tested
3. **Deterministic embeddings**: Used for testing without API key, may not reflect real semantic similarity
4. **Not statistically comprehensive**: Results may not generalize to larger document collections
5. **No real API calls**: Used mock results due to missing API key configuration
6. **Limited configuration space**: Only compared k values, did not test score thresholds or metadata filters
7. **Homogeneous document type**: All queries target the same document, may not reflect real-world diversity

## Future Improvements

To make this experiment more comprehensive:

1. **Expand test dataset**: Add more queries covering diverse document types
2. **Real API embeddings**: Use actual OpenAI embeddings for realistic similarity
3. **More configurations**: Test score thresholds, metadata filters, and hybrid approaches
4. **Larger document collection**: Test with multiple document types and sizes
5. **Statistical significance**: Use larger datasets for meaningful comparisons
6. **Cross-validation**: Use multiple query sets for robust evaluation
7. **Relevance scoring**: Implement more sophisticated relevance metrics beyond binary hit/miss

## Integration with RAG Pipeline

The selected configuration (k=3) can be used in the RAG pipeline:

```python
from healthcompass.vector_store import retrieve, initialize_vector_store

collection = initialize_vector_store()
results = retrieve(
    query="User question",
    collection=collection,
    k=3  # Best configuration from tuning experiment
)
```

The retrieved chunks can then be used as context for LLM generation with proper citation attribution.
