# Token-Aware Chunking Comparison

## Configuration

- Chunk size: 400 tokens
- Overlap: 60 tokens
- Overlap percentage: 15.0%
- Tokenizer: cl100k_base

## Chunk Statistics

| Strategy | Chunks | Avg Tokens | Min Tokens | Max Tokens | Total Tokens |
|----------|--------|------------|------------|------------|--------------|
| No overlap | 2 | 273.5 | 147 | 400 | 547 |
| 60-token overlap | 2 | 303.5 | 207 | 400 | 607 |

## Cost Comparison

- Additional chunks with overlap: 0
- Additional tokens with overlap: 60
- Percentage increase in tokens: 11.0%

## Sample Chunks (with overlap)

### Chunk 0

**Token count:** 400

**Source:** vaccination_guidance.txt

```
Vaccination Guidelines for Public Health Response

This document provides current approved guidance for vaccination protocols in public health emergencies. HealthCompass stores official public-health documents with versions, effective dates, geographic applicability, and approval status. Active and approved guidance should be preferred over superseded or expired documents.

Section 1: Core Vaccination Principles

Vaccination guidance should always be checked against the latest approved official version. Public health officials recommend following current guidelines from authoritative sources such as the CDC and WHO. Regular updates ensure that vaccination policies reflect the most recent scientific evidence and epidemiological data.

Healthcare providers must verify the approval status and effective dates of all vaccination protocols before implementation. Regional guidance may vary based on local epidemiological conditions and vaccine availability. Version control is essential for tracking policy changes and ensuring compliance with current standards.

Section 2: Priority Groups

High-risk populations include healthcare workers, elderly individuals, and those with underlying health conditions. These groups should be prioritized for vaccination according to current availability and epidemiological risk assessments. Priority frameworks may change based on emerging variants and supply chain considerations.

Essential workers and critical infrastructure personnel represent the second priority tier. Vaccination of these groups helps maintain societal functioning during public health emergencies. Geographic prioritization may be necessary when vaccine supply is limited relative to demand.

Section 3: Dosing and Administration

Standard dosing schedules must be followed unless specifically modified by public health authorities. Deviations from recommended protocols require documented justification and oversight. Dosing intervals should be optimized based on clinical trial data and real-world effectiveness studies.

Booster doses may be recommended based on waning immunity and emerging variant characteristics. The timing and composition of booster formulations should align with current scientific consensus and regulatory approval. Monitoring for adverse events remains essential throughout the vaccination campaign.

Section 4: Storage and Handling

Vaccine storage requirements must be strictly maintained to ensure product potency and safety. Cold chain protocols should be followed according to manufacturer specifications and regulatory guidelines. Temperature monitoring equipment must be calibrated
```

### Chunk 1

**Token count:** 207

**Source:** vaccination_guidance.txt

```
 scientific consensus and regulatory approval. Monitoring for adverse events remains essential throughout the vaccination campaign.

Section 4: Storage and Handling

Vaccine storage requirements must be strictly maintained to ensure product potency and safety. Cold chain protocols should be followed according to manufacturer specifications and regulatory guidelines. Temperature monitoring equipment must be calibrated and maintained according to established quality standards.

Proper handling procedures minimize vaccine wastage and ensure equitable distribution. Inventory management systems should track vaccine lots, expiration dates, and storage conditions throughout the supply chain. Contingency plans must address equipment failures and power outages.

Section 5: Monitoring and Surveillance

Post-vaccination monitoring systems should track both safety and effectiveness outcomes. Adverse event reporting mechanisms must be accessible to healthcare providers and the general public. Data collection systems should be designed to detect rare events and evaluate population-level impact.

Surveillance data should inform policy adjustments and communication strategies. Real-time monitoring enables rapid response to emerging safety signals or effectiveness concerns. Regular reporting to public health authorities supports evidence-based decision making and public trust.
```

## Boundary-Context Demonstration

The demonstration shows how overlap preserves context across chunk boundaries.

Without overlap, important information crossing the boundary is split between chunks.

With overlap, the boundary context appears in both neighboring chunks, ensuring that critical information is preserved for retrieval.

## Context Window Considerations

Retrieved context roughly depends on:

```
chunk_size × top_k
```

Plus:
- System instructions
- User question
- Other prompt content
- Generated answer budget

Therefore:
- Increasing chunk size reduces how many chunks can fit comfortably
- Increasing top-k increases retrieved token count
- Increasing overlap increases repeated tokens
- Chunk size, overlap, top-k, and context window should be tuned together

## Justification

### Chunk Size (400 tokens)

- Tokens are the model's actual unit rather than characters
- 400 tokens provides a reasonably sized retrieval unit
- Multiple retrieved chunks can fit into a model context window together with the system prompt, user question, and answer
- Smaller chunks improve retrieval precision but may lose context
- Larger chunks preserve more context but can reduce retrieval precision and increase token/embedding cost

### Overlap (60 tokens)

- 60 tokens provides approximately 15% overlap
- Overlap helps preserve ideas that cross chunk boundaries
- Too much overlap duplicates text and increases embedding/storage/retrieval cost
- Too little overlap increases the risk of losing boundary context

### HealthCompass Document Considerations

- Public-health guidance documents often contain procedural instructions that span multiple sentences
- Vaccination protocols include detailed dosing schedules that should not be split arbitrarily
- Advisories and SOPs contain critical safety information that must be preserved across boundaries
- Policy documents may have long sections that benefit from overlap to maintain context

