# RAG App Foundation

This project establishes a clean, isolated, reproducible workspace for an internal RAG assistant that serves a staff knowledge base.

## Project structure

```text
rag-app/
+-- data/                 # source documents (local-only)
+-- prompts/              # prompt templates
+-- outputs/              # logs and generated output
+-- src/                  # application source code
+-- .env.example          # sample env variables, committed
+-- .gitignore            # hides local-only files
+-- requirements.txt      # pinned Python dependencies
+-- README.md             # setup and verification notes
+-- .venv/                # local virtual environment, not committed
```

## Dependencies

The environment is isolated in `.venv` and dependency versions are captured in `requirements.txt`.

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
