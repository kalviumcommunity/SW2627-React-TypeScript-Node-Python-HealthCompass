# HealthCompass — RAG Foundation

HealthCompass is a RAG application for finding and verifying official public health guidance. The current implementation includes workspace setup, chat completion examples, and local TXT/PDF document loading.

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
│       └── ingestion/     # reusable TXT/PDF loader and JSON CLI
├── tests/
│   ├── fixtures/          # synthetic source documents
│   └── test_ingestion.py  # extraction and CLI contract tests
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
This smaller installation does not install the dependencies for `src/app.py`.
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
python -m pytest -q
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
DOCX, HTML, CSV, cleaning, chunking, indexing, and upload endpoints are future work.
The loader reads the whole file into memory and is intended for local intake;
future upload endpoints must enforce file-size limits.

## Testing and team workflow

```bash
python -m pytest -q
python -m compileall -q src
git diff --check
```

The document-loading suite currently contains 15 tests. It covers source identity,
metadata preservation, page positions, UTF-8 handling, invalid inputs, protected
PDFs, and CLI output/errors. CI also installs the full application dependencies,
compiles `src`, and checks chat configuration using placeholder credentials.

PDF fixtures are generated during tests, including multi-page, blank, and
password-protected documents. CI runs these tests without external API calls.
Keep real documents in ignored `data/`; commit only synthetic fixtures.

Use branches such as `feature/3.19-document-loading` and Conventional Commits
such as `feat(ingestion): add TXT and PDF document loading`. Keep each PR scoped
to one sprint deliverable and include its task number, behavior, limitations,
and validation results. Run `python -m pytest -q` before opening a PR.
