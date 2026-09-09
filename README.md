# HealthCompass — RAG Foundation

HealthCompass is a RAG application for finding and verifying official public health guidance. The current implementation includes workspace setup, chat completion examples, and local TXT/PDF document loading.

## Project structure

```text
rag-app/
+-- data/                 # source documents (local-only)
+-- prompts/              # prompt templates
+-- outputs/              # logs and generated output
+-- src/                  # application source code
+-- .env.example          # sample env variables, committed
+-- .gitignore            # hides local-only files
+-- requirements.txt      # Python dependencies
+-- README.md             # setup and verification notes
+-- .venv/                # local virtual environment, not committed
```

## Dependencies

The environment is isolated in `.venv` and dependency version ranges are declared in `requirements.txt`.

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> If your machine sits behind a certificate proxy or internal mirror, use:
>
> ```bash
> python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
> ```

This workspace keeps the dependency set intentionally small and reproducible for the application bootstrap so a fresh setup can install cleanly.

## Secrets and local config

Real secrets stay in a local `.env` file, never checked in. Copy the sample file and fill in your values:

```bash
copy .env.example .env
# or: cp .env.example .env
```

Example:

```env
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-real-key
CHAT_MODEL=gpt-4o-mini
EMBED_MODEL=text-embedding-3-small
```

## Run the app

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

## Verification

Clean-run verification: the virtual environment was created successfully, dependencies installed from `requirements.txt`, environment configuration was loaded from `.env`, and the project completed its startup/smoke test successfully.

This workspace was validated using a fresh local environment on 2026-09-08. The setup flow completed successfully and the app reported:

```text
Environment is configured for the RAG app.
Chat model: gpt-4o-mini
Embedding model: text-embedding-3-small
```

That confirms the project can be recreated from a clean machine by creating the venv, installing dependencies, copying `.env.example` to `.env`, and running the python entry point.


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

## Development layout and workflow

```text
src/
  app.py                    # existing chat examples
  healthcompass/
    ingestion/
      loader.py             # document contract and extraction
      cli.py                # local JSON inspection command
tests/
  fixtures/                 # synthetic, non-sensitive source documents
  test_ingestion.py         # extraction and CLI contract tests
pyproject.toml              # package, CLI, and test configuration
```

PDF fixtures are generated during tests, including multi-page, blank, and
password-protected documents. CI runs these tests without external API calls.
Keep real documents in ignored `data/`; commit only synthetic fixtures.

Use branches such as `feature/3.19-document-loading` and Conventional Commits
such as `feat(ingestion): add TXT and PDF document loading`. Keep each PR scoped
to one sprint deliverable and include its task number, behavior, limitations,
and validation results. Run `python -m pytest -q` before opening a PR.
