# HealthCompass — RAG Foundation

HealthCompass is a RAG application for finding and verifying official public health guidance. The current implementation includes workspace setup, chat completion examples with bounded history, parameter experiments, and local multi-format document loading (TXT, PDF, Markdown, HTML) with cleaning and character-based chunking.

## Project structure

```text
SW2627-React-TypeScript-Node-Python-HealthCompass/
├── .github/               # CI workflow
├── data/                  # local source documents, ignored by Git
├── outputs/               # placeholder for generated output
├── src/
│   ├── app.py             # chat completion and configuration examples
│   └── healthcompass/
│       ├── prompts/       # installed reusable prompt templates
│       ├── chat/          # bounded conversation history
│       └── ingestion/     # multi-format loading, cleaning, corpus intake, and JSON CLI
├── experiments/           # generation parameter comparisons and document intake demos
├── tests/
│   ├── fixtures/          # synthetic source documents
│   └── test_*.py          # ingestion, cleaning, chat, and experiment tests
├── .env.example           # configuration template
├── .gitignore
├── pyproject.toml         # package, CLI, ingestion dependencies, test settings
├── requirements.txt       # chat/vector dependencies and local package
└── README.md
```

## Local setup

Requires Python 3.11 or newer. Run commands from this repository's root.

macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the application dependencies and test tools:

```bash
python -m pip install -r requirements.txt -e ".[dev]"
```

For document loading and its tests only, use `python -m pip install -e ".[dev]"`.
This smaller installation does not install the dependencies for `src/app.py`
or the chat/experiment regression tests. Run only the ingestion and cleaning
tests with it: `python -m pytest -q tests/test_ingestion.py tests/test_cleaning.py tests/test_chunking.py`.
Dependency ranges are declared in `requirements.txt` and `pyproject.toml`;
there is currently no lockfile guaranteeing identical resolved versions.

## Secrets and local config

Configuration is required only for the chat examples. Document loading needs no
API credentials. Keep real secrets in a local `.env` file, never checked in.
Copy the template with `cp .env.example .env` on macOS/Linux or
`Copy-Item .env.example .env` in PowerShell, then fill in your provider values:

```env
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-real-key
CHAT_MODEL=your-chat-model
EMBED_MODEL=your-embedding-model
```

## Chat completion examples

```bash
python src/app.py
```

The default command checks the local configuration without making an API call. To
try the prompt roles and completion call, use one of these commands:

```bash
python src/app.py --prompt "What is our refund window?"
python src/app.py --compare
```

The app sends an explicit system message for role, scope, tone, and fallback
behavior, followed by the user prompt for the current task.

Chat requests use grounded-answer defaults: `temperature=0.1`, an output cap of
300 tokens, and `stop=["\\n\\nUser:"]`. Use `--temperature` for a different
randomness level, `--max-output-tokens` to change the output cap, repeat
`--stop` to provide custom stop sequences, or use `--top-p` instead of
temperature when tuning nucleus sampling. For example:

```bash
python src/app.py --prompt "What is our refund window?" --temperature 0 --max-output-tokens 150
```

## Context window management

`ConversationHistory` preserves the system message and removes complete oldest
user/assistant pairs. It rejects a newest turn that cannot fit, reserves 300 output
tokens within a default 6,000-unit context budget, and restores prior history when
a request fails. The estimate counts UTF-8 bytes plus message framing allowances;
it is deliberately conservative, not exact model tokenization or billing usage.
Set the budget below your provider's actual context limit. Tool calls and
multimodal messages are not supported by this text-only history manager.

```bash
python src/app.py --chat --context-budget 6000 --max-output-tokens 300
```

Enter `/exit` or EOF to quit. The output cap defaults to `max_completion_tokens`;
use `--token-limit-parameter max_tokens` only for providers requiring that field.
Use `--no-stop` to omit stop sequences for providers that do not support them.
See [parameter experiments](experiments/README.md) for repeated, measurable
comparisons of generation settings.

These examples currently use a generic internal-support system prompt, and
`--compare` uses refund-policy questions. They demonstrate API calls and message
roles; they do not retrieve uploaded documents or provide grounded HealthCompass
answers. Both model configuration values are currently required by the startup
validator, although the examples only call the chat model.

## Document loading — Sprint task 3.19

Requires Python 3.11+. From the repository root, install the project and test tools:

```bash
python -m pip install -e ".[dev]"
healthcompass-load tests/fixtures/guidance.txt --metadata '{"version":"1","region":"District A"}'
python -m pytest -q tests/test_ingestion.py tests/test_cleaning.py tests/test_chunking.py
```

The loader runs offline without API keys. It supports UTF-8 TXT (including a BOM),
Markdown (.md), HTML (.html, .htm), and text-based PDF via PyMuPDF. Output is a JSON
array with one record per PDF page, or one record for TXT/Markdown/HTML files:

- `document_id`: SHA-256 of the original file bytes; identifies file content,
  not the logical guideline or its editorial version.
- `source` and `filename`: resolved local path and original filename.
- `page_number`: one-based PDF page number; `null` for TXT/Markdown/HTML.
- `text`: extracted text, without additional cleaning or chunking.
- `metadata`: caller-supplied string fields such as version, authority, region,
  status, source URL, and effective date. These are preserved, not verified.

```python
from healthcompass.ingestion import load_document

pages = load_document("data/guidance.pdf", metadata={"version": "2"})
```

### Multi-format support

The loader converts different document formats to plain text for the RAG pipeline:

- **PDF**: Uses PyMuPDF to extract text from each page. Handles multi-page documents and preserves page numbers.
- **TXT**: Reads UTF-8 encoded text files with BOM support.
- **Markdown (.md)**: Reads UTF-8 encoded Markdown files, preserving formatting for downstream processing.
- **HTML (.html, .htm)**: Requires UTF-8, extracts text with block boundaries,
  and excludes head/script/style/template content. Invalid bytes are rejected.

TXT and Markdown line endings are preserved by loading; normalization belongs to
`--clean`. HTML parsing is text extraction, not an OCR or table reconstruction step.

### Corpus ingestion

For batch processing multiple documents, use the corpus ingestion function:

```python
from healthcompass.ingestion import ingest_corpus

result = ingest_corpus("data/", metadata={"version": "1"})
print(f"Loaded: {result.loaded_files} documents, {len(result.loaded)} pages")
print(f"Skipped: {len(result.skipped)} files")
```

Or use the demo script:

```bash
python experiments/document_intake.py data --corpus
```

The corpus ingestion recursively scans directories, loads all supported formats,
and continues after expected document-load failures. Files are processed in sorted
path order; skipped entries retain relative paths, so duplicate filenames remain
traceable. Symlinks are skipped. Unexpected programming errors are not hidden as
ordinary skipped files. The demo exits nonzero if any file is skipped or nothing
loads, while still printing the partial result.

### Source identity preservation

Every successfully loaded document preserves its source identity:

- Original filename is always available for RAG citations
- Full source path is retained for traceability
- Document ID (SHA-256 hash) identifies content uniquely
- Metadata preserves caller-supplied descriptive fields

### Error handling

The loader uses controlled exception handling:

- Blank PDF pages remain in output to preserve original positions
- Files with no extractable text, encrypted PDFs, invalid PDFs, missing files,
  unsupported formats, and invalid UTF-8 produce clear errors
- Corpus ingestion continues after individual file failures
- CLI failures write to stderr and exit with status 1
- Scanned pages require a future OCR step; partially scanned PDFs may contain
  blank extracted pages and need review

### Limitations

- PDF text extraction may fail or return little/no text for scanned/image-only PDFs
- OCR is not implemented; scanned PDFs require a future OCR step
- The loader reads whole files into memory; intended for local intake
- Future upload endpoints must enforce file-size limits
- DOCX, CSV, embeddings, indexing, and upload endpoints are future work

## Text cleaning — Sprint task 3.20

Cleaning is a separate, optional stage after extraction. Original loading output
is unchanged unless `--clean` is supplied:

```bash
healthcompass-load tests/fixtures/messy_guidance.txt --clean
healthcompass-load tests/fixtures/messy_guidance.txt --clean --remove-boilerplate-line "DRAFT HEADER" --remove-boilerplate-line "DRAFT FOOTER"
```

The cleaner normalizes Unicode to NFKC, line endings, horizontal whitespace, and
surplus blank lines. It preserves paragraphs, individual lines, list markers,
case, numbers, units, negations, and page boundaries. It does not reflow lines,
merge hyphenated words, guess OCR corrections, or infer which repeated lines are
boilerplate. Standard `Page N of M` footer lines are removed at page boundaries;
known custom headers and footers can be supplied explicitly. Whitespace-based
table column alignment is not retained; raw text remains available for review or
a future table-aware parser.

`--remove-boilerplate-line` removes exact, case-sensitive normalized lines only
at the beginning or end of each page. It is repeatable and requires `--clean`.
An identical line in the document body is preserved. Configure removal only for
known headers/footers; do not use it to remove substantive guidance.

Cleaned JSON retains `document_id`, source, filename, page number, and metadata.
`text` contains the cleaned version, with these additional fields:

- `original_text`: unmodified extracted text, before cleaning.
- `cleaning_version`: policy version, currently `2`.
- `removed_boilerplate_lines`: normalized boundary lines actually removed.
- `warnings`: includes `empty_after_cleaning` if a page has no remaining text.

Empty pages are retained for citation traceability. Cleaning never changes source
file bytes or their content hash. Downstream indexing should handle flagged empty
pages explicitly. Cleaned character offsets differ from raw extraction offsets;
page/source identity is preserved, but character-level citation mapping is not
implemented yet.

```python
from healthcompass.ingestion import clean_page, load_document

raw_pages = load_document("data/guidance.pdf", metadata={"version": "2"})
cleaned_pages = [clean_page(page, boilerplate_lines=["KNOWN HEADER"]) for page in raw_pages]
```

`clean_text()` is also available for standalone strings. Cleaning is idempotent
under the same policy. Re-cleaning a `CleanedPage` uses its original extraction,
allowing the removal policy to be changed without losing source text.

## Document chunking — Sprint task 3.21

```bash
healthcompass-load tests/fixtures/chunking_guidance.txt --clean --chunk --max-chars 160
healthcompass-load tests/fixtures/chunking_guidance.txt --clean --chunk --chunk-strategy fixed --max-chars 160
```

`--chunk` emits chunks instead of page records. It defaults to paragraph-aware
splitting with a 1,000-character limit. `--chunk-strategy` and `--max-chars` require
`--chunk`; cleaning remains separately opt-in. Without `--chunk`, loading and
cleaning retain their existing JSON output contracts.

```python
from healthcompass.ingestion import chunk_document, clean_page, load_document

pages = [clean_page(page) for page in load_document("data/guidance.pdf")]
chunks = chunk_document(pages, strategy="paragraph", max_chars=1000)
```

Each chunk retains source/page identity, metadata, a deterministic ID, and offsets
into its input text. Empty pages yield no chunks. See [chunking design and measured
comparison](docs/chunking.md) for limits, offset semantics, and the default choice.
The earlier single-page baseline retains character overlap; the bounded pipeline
adds no overlap.

## Token-aware chunking — Sprint task 3.23

Token-aware chunking uses tiktoken to size chunks by tokens rather than characters,
ensuring chunks respect the model's actual unit of processing.

```python
from healthcompass.ingestion import token_chunks, calculate_token_chunk_stats

chunks = token_chunks(
    text="Document text here...",
    source="guideline.pdf",
    filename="guideline.pdf",
    size=400,  # tokens
    overlap=60,  # tokens
)
stats = calculate_token_chunk_stats(chunks)
```

Run the comparison demonstration:

```bash
python experiments/token_chunking_comparison.py tests/fixtures/vaccination_guidance.txt
```

This generates a detailed report in `experiments/outputs/token_chunking_comparison.md`
with boundary-context demonstrations, chunk statistics, and cost trade-offs.

### Configuration

- **Chunk size**: 400 tokens (default)
- **Overlap**: 60 tokens (default, 15% overlap)
- **Tokenizer**: cl100k_base (OpenAI's tokenizer)

### Why token-based sizing?

- Tokens are the model's actual unit rather than characters
- Character-based sizing can produce unpredictable token counts
- Token-aware sizing ensures consistent context window usage
- Multiple retrieved chunks can fit into model context alongside prompts

### Overlap benefits

- Preserves ideas that cross chunk boundaries
- Ensures critical information is not lost at boundaries
- Trade-off: increases storage and retrieval cost through repeated tokens

### Boundary-context demonstration

The comparison script demonstrates how overlap preserves context:
- Without overlap: important information crossing boundaries is split between chunks
- With overlap: boundary context appears in both neighboring chunks

See the generated report for actual examples and chunk statistics.

## Embeddings — Sprint task 3.26

Embeddings convert text chunks into numerical vectors for semantic search using OpenAI-compatible APIs.

```python
from healthcompass.ingestion import (
    generate_embeddings,
    prepare_chunks_from_token_chunks,
    token_chunks,
)

# Create chunks from text
chunks = token_chunks(
    text="Document text here...",
    source="guideline.pdf",
    filename="guideline.pdf",
    size=400,
    overlap=60,
)

# Prepare for embedding
prepared_chunks = prepare_chunks_from_token_chunks(chunks)

# Generate embeddings
result = generate_embeddings(prepared_chunks, batch_size=100)
```

Run the embedding generation script:

```bash
python experiments/embeddings/generate_embeddings.py
```

### Configuration

Embeddings use environment variables:

- **OPENAI_API_KEY**: Required API key for embeddings service
- **EMBEDDING_MODEL**: Model name (default: `text-embedding-3-small`)
- **OPENAI_BASE_URL**: API base URL (default: `https://api.openai.com/v1`)
- **EMBEDDING_BATCH_SIZE**: Batch size for processing (default: 64)
- **MAX_RETRY_ATTEMPTS**: Maximum retry attempts for temporary failures (default: 3)

### Why embeddings?

- Convert text to numerical vectors for semantic similarity search
- Enable retrieval of relevant document chunks based on meaning, not just keywords
- Support both document chunks and user queries using the same embedding model
- Foundation for RAG systems to find contextually relevant information

### Model configuration through environment variables

- API keys are never hardcoded, preventing credential exposure
- Different environments (dev, staging, production) can use different models/providers
- Same model must be used for both document chunks and queries for consistency
- Allows easy switching between embedding models without code changes

### Vector storage with metadata

Each embedded chunk stores:
- Original text for citation and display
- Source document and filename for traceability
- Chunk index for position within document
- Metadata (section, version, region, etc.)
- Embedding vector for similarity search
- Embedding model name for reproducibility

### Vector dimension

- Represents the number of dimensions in the semantic space
- Different models produce different dimensions (e.g., 1536 for text-embedding-3-small)
- Higher dimensions can capture more semantic nuance but increase storage/computation cost
- Dimension is read from actual API response, not assumed

### Batch processing

- Processes multiple chunks in a single API call to reduce overhead
- Configurable batch size balances API latency and error handling
- Batching reduces total API calls and cost for large corpora
- Failed batches can be retried without reprocessing successful batches

### Cost and performance considerations

- Cost scales with number of chunks and API pricing model
- Latency increases with corpus size and batch size
- Larger vector dimensions increase storage and computation cost
- Batching reduces API overhead but increases per-request complexity
- Consider incremental embedding for large, growing document collections

### Batch embedding management

The enhanced embedding pipeline includes:

- **Batch processing**: Configurable batch size (default: 64) reduces API calls
- **Skip existing embeddings**: Content-based chunk IDs prevent redundant API calls
- **Retry with exponential backoff**: Handles temporary failures automatically
- **Progress saving**: Incremental saves enable resumability for large corpora
- **Run summary**: Comprehensive statistics including cost estimation
- **Resumability**: Can continue from partially completed runs

### How batch size works

- Batch size determines how many chunks are processed in a single API call
- Larger batches reduce API overhead but increase memory usage and per-request complexity
- Default batch size of 64 provides good balance for most use cases
- Adjust based on your corpus size and API rate limits

### How existing embeddings are skipped

- Each chunk generates a unique ID based on its content and metadata
- Before processing, the pipeline checks if a chunk ID already exists in the output file
- Chunks with existing embeddings are skipped, reducing API calls and cost
- This enables efficient re-runs when adding new documents to an existing corpus

### How retries and backoff work

- Temporary failures (rate limits, timeouts, connection errors) trigger automatic retry
- Exponential backoff sequence: 1, 2, 4, 8 seconds between attempts
- Maximum retry attempts configurable via `MAX_RETRY_ATTEMPTS` (default: 3)
- Permanent errors (missing API keys, invalid configuration) fail immediately without retry
- Failed batches are recorded in the run summary for troubleshooting

### How progress is saved and resumed

- Embeddings are saved incrementally after each successful batch
- Uses atomic file operations (write to temp file, then rename) to prevent corruption
- If the process stops, it can continue from where it left off
- Existing embeddings are never deleted during re-runs
- Enables processing of large corpora without risking complete data loss

### How approximate cost is calculated

- Cost estimation based on token count and model pricing
- Rough token estimation: ~4 characters per token
- Example pricing (text-embedding-3-small): $0.02 per 1M tokens
- Result is clearly labeled as estimated (actual cost may vary)
- Helps budget and plan large-scale embedding operations

## Vector Database — Sprint task 3.30

HealthCompass uses ChromaDB as a vector database to store document embeddings alongside their source text and metadata for efficient semantic search and retrieval.

```python
from healthcompass.vector_store import (
    initialize_vector_store,
    get_vector_store_config,
    VectorRecord,
    insert_record,
    get_record,
)

# Get configuration from environment variables
config = get_vector_store_config()

# Initialize database (creates directory and collection if needed)
collection = initialize_vector_store(config)

# Insert a record
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

# Retrieve a record
retrieved = get_record(collection, "chunk_001")
```

Run the insert and readback test:

```bash
python experiments/vector_db_readback.py
```

### Configuration

Vector database uses environment variables:

- **CHROMA_DB_PATH**: Database storage path (default: `data/chroma_db`)
- **CHROMA_COLLECTION_NAME**: Collection name (default: `healthcompass_documents`)
- **EMBEDDING_MODEL**: Embedding model (determines vector dimension, default: `text-embedding-3-small`)

### Why use a vector database?

- **Semantic Search**: Find documents similar in meaning, not just keyword matches
- **Scalability**: Efficiently handle millions of vectors with fast similarity search
- **Integration**: Seamlessly works with embedding models for RAG applications
- **Metadata Support**: Store rich metadata alongside vectors for filtering and context

### Vector dimension and model compatibility

The vector dimension of the collection must match the embedding model used:

| Model | Dimension |
|-------|-----------|
| text-embedding-3-small | 1536 |
| text-embedding-3-large | 3072 |
| text-embedding-ada-002 | 1536 |

The vector store automatically configures the correct dimension based on the `EMBEDDING_MODEL` environment variable.

### Record schema

Each record contains:
- **id**: Unique identifier for the record
- **embedding**: The high-dimensional vector representing the text
- **text**: The original source text for the chunk
- **metadata**: Rich metadata including source, filename, chunk_id, section, page_number, document_type

### Why store text and metadata with vectors?

- **Citation**: Accurately cite sources when generating answers
- **Context**: Provide full context when retrieving similar documents
- **Verification**: Ensure retrieved content matches user queries
- **Filtering**: Filter results by metadata (e.g., specific documents, sections)
- **Debugging**: Trace retrieval results back to source documents

### Running tests

Unit tests use temporary databases and deterministic test vectors:

```bash
pytest tests/test_vector_database.py -v
```

Integration test for insert and readback:

```bash
python experiments/vector_db_readback.py
```

This generates a report in `experiments/outputs/vector_db_readback.md` with actual test results.

### Health check

Verify database connectivity:

```python
from healthcompass.vector_store import health_check

if health_check():
    print("Vector database is accessible and healthy")
```

### Troubleshooting

**Dimension mismatch error**: The existing collection has a different vector dimension than the configured embedding model. Options:
1. Delete and recreate the collection (WARNING: deletes all data): `rm -rf data/chroma_db`
2. Use the same embedding model that was used to create the collection
3. Create a new collection with a different name

**Collection already exists**: The vector store automatically loads existing collections instead of creating new ones to prevent accidental data loss. To start fresh, delete the database directory or use a different collection name.

See [vector database documentation](docs/vector_database.md) for detailed information.

## Similarity Search and Top-K Retrieval — Sprint task 3.32

HealthCompass uses semantic similarity search to retrieve the most relevant document chunks for user queries using the vector database.

```python
from healthcompass.vector_store import retrieve, initialize_vector_store, embed_query

# Initialize database
collection = initialize_vector_store()

# Retrieve top 3 most similar chunks
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

Run the retrieval demonstration:

```bash
python experiments/retrieval_demo.py
```

### Retrieval Process

The retrieval pipeline follows this process:

1. **User Query**: Natural language question from the user
2. **Query Embedding**: Convert query to vector using the same embedding model as documents
3. **Vector Search**: Search vector database for semantically similar chunks
4. **Ranked Results**: Return top-k chunks with distance scores and metadata

### Why Top-K?

Top-k retrieval returns the k most similar document chunks:

- **k=1**: Fast, minimal context, focused answers
- **k=3**: Balanced approach (default), good context vs noise trade-off
- **k=5**: More context, comprehensive answers, may include less relevant chunks
- **k=10**: Extensive context for complex queries

### Distance Score

The system uses **cosine distance** as the similarity metric:

- **Range**: 0.0 to 2.0 for normalized vectors
- **Lower values** indicate higher similarity (closer in semantic space)
- **0.0**: Perfect semantic match
- **~0.3-0.5**: Strong semantic similarity
- **>1.0**: Low similarity or unrelated content

**Important**: Lower distance = higher similarity (opposite of similarity scores).

### Retrieved Result Schema

Each result includes:
- **rank**: Position in results (1 = most similar)
- **chunk_id**: Unique identifier for the chunk
- **distance**: Cosine distance (lower = more similar)
- **text**: Original chunk text for context
- **metadata**: Source information (document, filename, chunk_id, section, page_number, document_type)

### Configuration

Retrieval uses the same environment variables as embeddings:

- **OPENAI_API_KEY**: Required for query embedding
- **EMBEDDING_MODEL**: Must match the model used for document embeddings
- **CHROMA_DB_PATH**: Vector database storage path
- **CHROMA_COLLECTION_NAME**: Collection name for search

### Why Query and Document Embeddings Must Use the Same Model

Embeddings from different models live in different semantic spaces. Using the same model ensures:

- Query and document embeddings are comparable
- Distance scores accurately reflect semantic similarity
- Retrieval behavior is predictable and reproducible

If documents use `text-embedding-3-small` (1536 dimensions) but queries use `text-embedding-3-large` (3072 dimensions), the vectors are incompatible and similarity calculations are meaningless.

### Running Tests

Unit tests for retrieval with mocked API calls:

```bash
pytest tests/test_vector_database.py -k "retrieve or embed" -v
```

Integration test for retrieval with different k values:

```bash
python experiments/retrieval_demo.py
```

This generates a report in `experiments/outputs/retrieval_results.md` with actual test results for k=1, k=3, and k=5.

### Error Handling

- **Missing API key**: Clear error message requiring OPENAI_API_KEY configuration
- **Empty collection**: Error message requiring document insertion first
- **Invalid k**: Validation ensures k > 0
- **Dimension mismatch**: Automatic detection and clear error reporting

See [retrieval documentation](docs/retrieval.md) for detailed information.

### Validation

The embedding generation includes comprehensive validation:
- All chunks receive an embedding
- Each embedding is a list of numeric values
- All vectors have the same dimension
- Number of vectors matches number of chunks
- Each vector remains attached to its source text and metadata

### Sample output

The script generates:
- `experiments/outputs/embedded_chunks.json` - Complete embedded chunks with vectors
- `experiments/outputs/embedding_sample.md` - Human-readable sample report

## Testing and team workflow

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m compileall -q src experiments
git diff --check
```

The test suite covers chat history, experiment request/report handling, extraction,
cleaning, metadata preservation, page positions, Unicode, invalid inputs, protected
PDFs, and CLI output/errors. All API tests use mocked responses. CI installs the full application dependencies,
checks lint and formatting, runs tests, compiles `src` and `experiments`, and checks
chat configuration using placeholder credentials.

PDF fixtures are generated during tests, including multi-page, blank, and
password-protected documents. CI runs these tests without external API calls.
Keep real documents in ignored `data/`; commit only synthetic fixtures.

Use branches such as `feature/3.21-document-chunking` and Conventional Commits
such as `feat(ingestion): add document chunking strategies`. Keep each PR scoped
to one sprint deliverable and include its task number, behavior, limitations,
and validation results. Run `python -m pytest -q` before opening a PR.
