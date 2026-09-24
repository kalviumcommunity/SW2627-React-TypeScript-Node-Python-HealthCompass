# Retrieval Tuning Experiment

## Dataset

- **Number of queries:** 8
- **Expected source methodology:** Source document matching
- **Keyword matching:** Fallback when source not found

## Configuration Comparison

| Configuration | k | Top-1 Hit Rate | Top-k Hit Rate | Average Rank |
|---|---:|---:|---:|---:|
| Config A | 3 | 100.0% | 100.0% | 1.00 |
| Config B | 5 | 100.0% | 100.0% | 1.00 |

## Detailed Results

### Config A

**Settings:**
- k: 3
- Score threshold: None
- Metadata filter: None

**Performance:**
- Top-1 hits: 8/8
- Top-k hits: 8/8
- Top-1 hit rate: 100.0%
- Top-k hit rate: 100.0%
- Average rank: 1.00
- Queries with zero relevant: 0

**Query Results:**

✓ **Query:** What are the priority groups for vaccination?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** How should vaccines be stored and handled?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** What are the core vaccination principles?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** How should dosing and administration be managed?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** What monitoring and surveillance systems are needed?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** Who should be prioritized for vaccination during emergencies?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** What are the cold chain requirements for vaccines?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** How should vaccine effectiveness be monitored?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

### Config B

**Settings:**
- k: 5
- Score threshold: None
- Metadata filter: None

**Performance:**
- Top-1 hits: 8/8
- Top-k hits: 8/8
- Top-1 hit rate: 100.0%
- Top-k hit rate: 100.0%
- Average rank: 1.00
- Queries with zero relevant: 0

**Query Results:**

✓ **Query:** What are the priority groups for vaccination?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** How should vaccines be stored and handled?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** What are the core vaccination principles?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** How should dosing and administration be managed?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** What monitoring and surveillance systems are needed?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** Who should be prioritized for vaccination during emergencies?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** What are the cold chain requirements for vaccines?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

✓ **Query:** How should vaccine effectiveness be monitored?
  - Expected source: vaccination_guidance.txt
  - Retrieved rank: 1
  - Retrieved source: vaccination_guidance.txt
  - Score: 0.1000
  - Matched: True

## Best Configuration

**Chosen configuration:** Config A
- k = 3
- Score threshold = None
- Metadata filter = None

**Reason:**
Selected based on highest top-k hit rate (100.0%) and top-1 hit rate (100.0%). Configuration with k=3 provides better recall while maintaining reasonable context size.

## Limitations

- Small evaluation dataset (8 queries)
- Single document type (vaccination guidance)
- Deterministic embeddings used for testing
- Not a statistically comprehensive benchmark
- Results may vary with different document collections
