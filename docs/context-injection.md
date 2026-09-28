# Context Injection & Prompt Augmentation

This document explains the context injection and prompt augmentation system for HealthCompass, which prepares retrieved document chunks for LLM generation with proper source tracking and token budget management.

## What is Context Injection?

Context injection is the process of taking retrieved document chunks from a vector database and formatting them into a structured context that can be provided to a language model along with a user question. This is a critical component of Retrieval-Augmented Generation (RAG) systems.

## Why Retrieved Chunks Need Source Markers

Source markers serve several important purposes:

1. **Citation Tracking**: They allow the final answer to identify where information came from
2. **Auditability**: They enable verification of information sources
3. **Grounding**: They help prevent the model from hallucinating information not in the provided context
4. **User Trust**: They provide transparency about the source of information

Each chunk is formatted with a marker like `[1] vaccination_guidance.txt#0` where:
- `[1]` is the retrieval rank
- `vaccination_guidance.txt` is the source document
- `#0` is the chunk index within the document

## Why the Context Needs a Token Budget

Language models have limits on the amount of text they can process in a single request (context window). The token budget ensures:

1. **Prevents Overflow**: Avoids exceeding the model's context window
2. **Cost Control**: Limits the number of tokens sent to the API (reducing costs)
3. **Performance**: Smaller contexts can improve response times
4. **Quality**: Focusing on the most relevant chunks improves answer quality

The default budget is 5000 tokens, configurable via the `MAX_CONTEXT_TOKENS` environment variable.

## How the System Decides Which Chunks Fit

The context assembly process follows these steps:

1. **Process in Retrieval Order**: Chunks are considered in their retrieval ranking order
2. **Format with Source Marker**: Each chunk is formatted with its source marker
3. **Count Tokens**: The token count of the formatted chunk is calculated
4. **Check Budget**: If adding the chunk would exceed the remaining budget, it's excluded
5. **Stop**: Continues until budget is exhausted or all chunks are processed

This ensures that the most relevant chunks (highest ranked) are included first.

## System Instructions Tell the Model to Answer Only from Context

The system instruction explicitly tells the model:

```
You are a grounded assistant.
Answer the question using only the provided context.
Do not use outside knowledge.
If the answer cannot be found in the provided context, say:
'I don't have enough information in the provided context.'
When possible, cite the source markers such as [1] or [2].
```

This instruction:

- **Prevents Hallucination**: Encourages the model to stick to provided information
- **Enables Grounding**: Requires citations to source markers
- **Handles Missing Information**: Provides a clear response when context is insufficient
- **Improves Accuracy**: Reduces the chance of fabricating information

## What Happens When Context Does Not Contain the Answer

When the provided context doesn't contain information to answer the question, the model is instructed to respond:

```
I don't have enough information in the provided context.
```

This is a critical safety feature that prevents the model from:

- Hallucinating incorrect information
- Making up sources
- Providing misleading answers
- Using outside knowledge that may be outdated or incorrect

## How Source Markers Help Auditing and Citations

Source markers enable several important capabilities:

1. **Verification**: Users can verify information by checking the original source
2. **Debugging**: Developers can trace which chunks contributed to an answer
3. **Compliance**: Audit trails can show which documents were used
4. **Transparency**: Users understand where information comes from
5. **Accountability**: Sources can be identified for fact-checking

## The RAG Pipeline: Retrieval → Context Assembly → Augmented Prompt → Generation

The complete RAG pipeline follows this flow:

```
User Question
    ↓
Retrieval (Vector Search)
    ↓
Ranked Chunks
    ↓
Context Assembly (Token Budget)
    ↓
Formatted Context with Source Markers
    ↓
Augmented Prompt (Instructions + Context + Question)
    ↓
LLM Generation
    ↓
Grounded Answer with Citations
```

### Step 1: Retrieval
- User question is embedded using the same model as document chunks
- Vector search finds semantically similar chunks
- Results are ranked by similarity (distance)

### Step 2: Context Assembly
- Chunks are formatted with source markers
- Token budget is applied
- Chunks are included until budget is exhausted
- Source metadata is tracked

### Step 3: Augmented Prompt
- System instructions are added
- Formatted context is inserted
- User question is appended
- Complete prompt is sent to LLM

### Step 4: Generation
- LLM processes the augmented prompt
- Answer is generated using only provided context
- Source markers are cited where possible
- Grounded response is returned

## Implementation Details

### Core Functions

The implementation provides these key functions:

- `format_chunk_with_source()`: Formats a chunk with source marker
- `count_tokens()`: Counts tokens using tiktoken
- `assemble_context()`: Assembles context with token budget
- `build_augmented_prompt()`: Creates the complete augmented prompt
- `get_max_context_tokens()`: Gets configured token budget

### Data Structures

- `ContextAssemblyResult`: Contains assembled context and metadata
- `AugmentedPromptResult`: Contains complete prompt and metadata

### Configuration

Environment variables:
- `MAX_CONTEXT_TOKENS`: Maximum tokens for context (default: 5000)

### Tokenizer

The system uses tiktoken with the `cl100k_base` encoding, which is the same encoding used by OpenAI's GPT models. This ensures accurate token counting for API calls.

## Running the Demonstration

To see the context injection system in action:

```bash
python experiments/context_injection_demo.py
```

This will:

1. Retrieve chunks for a sample question
2. Demonstrate token budget behavior with a small budget
3. Show normal token budget usage
4. Display source marker formatting
5. Generate an augmented prompt
6. Save results to `experiments/outputs/context_injection_results.md`

## Example Output

### Sample Question
```
What are the priority groups for vaccination?
```

### Source Markers
```
[1] vaccination_guidance.txt#0
[2] vaccination_guidance.txt#1
```

### Token Budget Behavior
With a 300-token budget:
- Retrieved chunks: 2
- Included chunks: 1
- Excluded chunks: 1
- Context tokens: 217 / 300

### Augmented Prompt Structure
```
You are a grounded assistant.
Answer the question using only the provided context.
Do not use outside knowledge.
If the answer cannot be found in the provided context, say:
'I don't have enough information in the provided context.'
When possible, cite the source markers such as [1] or [2].

Context:
[1] vaccination_guidance.txt#0
...

Question:
What are the priority groups for vaccination?
```

## Testing

Unit tests cover:

- Source marker formatting correctness
- Multiple chunk formatting
- Token budget enforcement
- Chunk exclusion when budget exceeded
- Token calculation accuracy
- Source metadata tracking
- Empty retrieval handling
- Large chunk handling
- Retrieval order preservation
- Augmented prompt structure

Run tests with:
```bash
pytest tests/test_context_injection.py
```

## Limitations

- Deterministic embeddings are used for demonstration when no API key is available
- Small document collection (2 chunks) limits demonstration scope
- Token budget is fixed per request (not adaptive)
- Source markers assume certain metadata fields exist

## Future Improvements

Potential enhancements:

- Adaptive token budget based on question complexity
- More sophisticated chunk selection strategies
- Support for multiple tokenizers
- Re-ranking based on token budget constraints
- Parallel context assembly for large collections
- Source marker customization options
