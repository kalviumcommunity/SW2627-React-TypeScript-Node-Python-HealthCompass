# Chunking Strategy Comparison

**Document:** tests/fixtures/vaccination_guidance.txt

## Statistics Comparison

Strategy              Chunk Count    Avg Size    Min Size    Max Size
--------------------------------------------------------------
Fixed-size + overlap  9              489        399        500       
Paragraph-based       17             210        26         329       

## Sample Chunks

# Fixed-size + overlap

### Chunk 0

**Length:** 500 characters
**Source:** vaccination_guidance.txt

```
Vaccination Guidelines for Public Health Response

This document provides current approved guidance for vaccination protocols in public health emergencies. HealthCompass stores official public-health documents with versions, effective dates, geographic applicability, and approval status. Active and approved guidance should be preferred over superseded or expired documents.

Section 1: Core Vaccination Principles

Vaccination guidance should always be checked against the latest approved official 
```

### Chunk 1

**Length:** 500 characters
**Source:** vaccination_guidance.txt

```
tion Principles

Vaccination guidance should always be checked against the latest approved official version. Public health officials recommend following current guidelines from authoritative sources such as the CDC and WHO. Regular updates ensure that vaccination policies reflect the most recent scientific evidence and epidemiological data.

Healthcare providers must verify the approval status and effective dates of all vaccination protocols before implementation. Regional guidance may vary base
```

### Chunk 2

**Length:** 500 characters
**Source:** vaccination_guidance.txt

```
 effective dates of all vaccination protocols before implementation. Regional guidance may vary based on local epidemiological conditions and vaccine availability. Version control is essential for tracking policy changes and ensuring compliance with current standards.

Section 2: Priority Groups

High-risk populations include healthcare workers, elderly individuals, and those with underlying health conditions. These groups should be prioritized for vaccination according to current availability a
```

*... and 6 more chunks*

# Paragraph-based

### Chunk 0

**Length:** 49 characters
**Source:** vaccination_guidance.txt

```
Vaccination Guidelines for Public Health Response
```

### Chunk 1

**Length:** 324 characters
**Source:** vaccination_guidance.txt

```
This document provides current approved guidance for vaccination protocols in public health emergencies. HealthCompass stores official public-health documents with versions, effective dates, geographic applicability, and approval status. Active and approved guidance should be preferred over superseded or expired documents.
```

### Chunk 2

**Length:** 38 characters
**Source:** vaccination_guidance.txt

```
Section 1: Core Vaccination Principles
```

*... and 14 more chunks*

## Trade-off Analysis

### Fixed-size + overlap

**Advantages:**
- Predictable chunk sizes
- Works well with long documents
- Overlap helps preserve context across boundaries
- Useful when paragraphs are extremely long or inconsistent

**Disadvantages:**
- Can split sentences/paragraphs
- May reduce semantic coherence
- Overlap creates some duplicated text

### Paragraph-based

**Advantages:**
- Preserves natural semantic boundaries
- Easier for humans to inspect
- Paragraphs usually represent a coherent idea

**Disadvantages:**
- Chunk sizes can vary significantly
- Very long paragraphs may still exceed useful retrieval size
- Very short paragraphs can produce tiny chunks

## Recommended Strategy

**Recommended strategy:** Fixed-size + overlap

**Reason:** The document contains very short paragraphs (minimum: 26 chars) that would produce tiny chunks lacking context for effective retrieval.

## Context Window Relationship

Chunk size relates to the context window in several important ways:

- The context window is the maximum amount of text/tokens the model can process in one request
- Chunks should be small enough that multiple retrieved chunks plus the user's question and system instructions fit comfortably
- Very large chunks waste context space and can reduce retrieval precision
- Very small chunks may lose necessary context
- Chunk size should therefore leave room for multiple relevant chunks and the generated answer

For HealthCompass, with typical context windows of 4K-8K tokens, chunk sizes of 500-1000 characters balance context preservation with retrieval precision.