# HealthCompass — RAG Foundation

HealthCompass is a RAG application for finding and verifying official public health guidance. The current implementation includes workspace setup, chat completion examples with bounded history, parameter experiments, and local TXT/PDF document loading and cleaning.

## Project structure

```text
SW2627-React-TypeScript-Node-Python-HealthCompass/
├── .github/               # CI workflow and PR template
├── data/                  # local source documents, ignored by Git
├── prompts/               # placeholder for future prompt templates
├── outputs/               # placeholder for generated output
├── src/
│   ├── app.py             # chat completion and configuration examples
│   └── healthcompass/
│       ├── chat/          # bounded conversation history
│       └── ingestion/     # TXT/PDF loading, cleaning, and JSON CLI
├── experiments/           # generation parameter comparisons
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
tests with it: `python -m pytest -q tests/test_ingestion.py tests/test_cleaning.py`.
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

## Context window management

`ConversationHistory` preserves the system message and removes complete oldest
user/assistant pairs. It rejects a newest turn that cannot fit, reserves 512 output
tokens within a default 6,000-unit context budget, and restores prior history when
a request fails. The estimate counts UTF-8 bytes plus message framing allowances;
it is deliberately conservative, not exact model tokenization or billing usage.
Set the budget below your provider's actual context limit. Tool calls and
multimodal messages are not supported by this text-only history manager.

```bash
python src/app.py --chat --context-budget 6000 --max-output-tokens 512
```

Enter `/exit` or EOF to quit. The output cap defaults to `max_completion_tokens`;
use `--token-limit-parameter max_tokens` only for providers requiring that field.
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
python -m pytest -q tests/test_ingestion.py tests/test_cleaning.py
```

The loader runs offline without API keys. It supports UTF-8 TXT (including a BOM)
and text-based PDF via PyMuPDF. Output is a JSON array with one record per PDF
page, or one record for a TXT file:

- `document_id`: SHA-256 of the original file bytes; identifies file content,
  not the logical guideline or its editorial version.
- `source` and `filename`: resolved local path and original filename.
- `page_number`: one-based PDF page number; `null` for TXT.
- `text`: extracted text, without additional cleaning or chunking.
- `metadata`: caller-supplied string fields such as version, authority, region,
  status, source URL, and effective date. These are preserved, not verified.

```python
from healthcompass.ingestion import load_document

pages = load_document("data/guidance.pdf", metadata={"version": "2"})
```

Blank PDF pages remain in the output to preserve original positions. Files with
no extractable text, encrypted PDFs requiring a password, invalid PDFs, missing
files, unsupported formats, and invalid UTF-8 produce clear errors. CLI failures
write to stderr and exit with status 1. Scanned pages require a future OCR step;
partially scanned PDFs may contain blank extracted pages and need review.
DOCX, HTML, CSV, chunking, indexing, and upload endpoints are future work.
The loader reads the whole file into memory and is intended for local intake;
future upload endpoints must enforce file-size limits.

## Text cleaning — Sprint task 3.20

Cleaning is a separate, optional stage after extraction. Original loading output
is unchanged unless `--clean` is supplied:

```bash
healthcompass-load tests/fixtures/messy_guidance.txt --clean
healthcompass-load tests/fixtures/messy_guidance.txt --clean --remove-boilerplate-line "DRAFT HEADER" --remove-boilerplate-line "DRAFT FOOTER"
```

The cleaner normalizes Unicode to NFC, line endings, horizontal whitespace, and
surplus blank lines. It preserves paragraphs, individual lines, list markers,
case, numbers, units, negations, and page boundaries. It does not reflow lines,
merge hyphenated words, guess OCR corrections, or infer which repeated lines are
boilerplate. Whitespace-based table column alignment is not retained; raw text
remains available for review or a future table-aware parser.

`--remove-boilerplate-line` removes exact, case-sensitive normalized lines only
at the beginning or end of each page. It is repeatable and requires `--clean`.
An identical line in the document body is preserved. Configure removal only for
known headers/footers; do not use it to remove substantive guidance.

Cleaned JSON retains `document_id`, source, filename, page number, and metadata.
`text` contains the cleaned version, with these additional fields:

- `original_text`: unmodified extracted text, before cleaning.
- `cleaning_version`: policy version, currently `1`.
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

Use branches such as `feature/3.20-text-cleaning` and Conventional Commits
such as `feat(ingestion): add source-preserving text cleaning`. Keep each PR scoped
to one sprint deliverable and include its task number, behavior, limitations,
and validation results. Run `python -m pytest -q` before opening a PR.
