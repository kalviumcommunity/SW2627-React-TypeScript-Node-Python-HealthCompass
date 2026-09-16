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
adds no overlap. Token-aware sizing, embeddings, and retrieval remain future work.

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
