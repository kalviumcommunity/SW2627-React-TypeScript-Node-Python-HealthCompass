# LLM parameter experiments — Task 3.16

This runner compares temperature, output limits, top-p, and stop sequences using
the same synthetic HealthCompass context. Each setting gets three trials by
default (36 API calls total). One generation control varies per comparison;
top-p trials leave temperature at the provider default.

## Run

Install the full application and test dependencies from the repository root:

```bash
python -m pip install -r requirements.txt -e ".[dev]"
python experiments/parameter_experiments.py --dry-run
```

A dry run prints the plan only. To measure real responses, configure
`OPENAI_API_KEY`, `CHAT_MODEL`, and optionally `OPENAI_BASE_URL` in `.env`, then:

```bash
python experiments/parameter_experiments.py --output outputs/parameter-run-1.json
```

Use a chat model supporting the selected controls. The default output cap uses
`max_completion_tokens`; compatible providers requiring the older field can use
`--token-limit-parameter max_tokens`. Unsupported parameters are recorded as
errors; the runner does not silently change the experiment or model.
Use `--repetitions 2` for 24 calls. API calls may incur provider charges.
Each call has a 30-second timeout and automatic SDK retries are disabled.

## Evidence and interpretation

The JSON report contains the prompt, exact settings, requested/returned model,
timestamps, fingerprint when supplied, response text, finish reason, and reported
usage. Derived comparisons include success/failure counts, distinct outputs,
length-limited responses, mean completion tokens, and marker presence.

- Temperature zero does not guarantee identical results. Compare repeated outputs.
- `finish_reason=length` indicates the output cap was reached; `stop` alone does
  not distinguish natural completion from a configured stop sequence.
- Missing usage stays null and is excluded from averages, not treated as zero.
- Failed requests never count as successful observations. Any failed trial gives
  the command a nonzero exit code after recording the results.
- These measurements do not establish answer correctness or grounding quality.
- No optimal production settings are claimed without a measured evaluation.

Reports refuse to overwrite existing paths. Local JSON reports are ignored by
Git; review and redact them before deliberately sharing measured evidence.
The older files under `experiments/outputs/` are explicitly labelled placeholders,
not completed experiments. No live measurements were available during the review.
Tests use synthetic mocked API responses and do not count as live experiments.

Parameter semantics and model-specific restrictions are documented in the
[official Chat Completions API reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create).
