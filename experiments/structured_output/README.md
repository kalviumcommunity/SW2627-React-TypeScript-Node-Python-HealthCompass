# Structured output — Task 3.17

Compare JSON mode with a prompt-only response and validate the returned data
locally. This is an experiment, not an integrated RAG answer endpoint.

## Run from the repository root

```bash
python -m pip install -r requirements.txt -e ".[dev]"
python -m experiments.structured_output.structured_output --dry-run
python -m experiments.structured_output.structured_output --repetitions 3
```

Live runs require `OPENAI_API_KEY` and `CHAT_MODEL`; `OPENAI_BASE_URL` is optional.
The configured model/provider must support JSON mode, temperature and `max_tokens`.
Three repetitions per mode make six API calls. Calls use a 30-second timeout
and disable automatic SDK retries. No live results are claimed by the test suite.

## Validation and recovery

`answer` and `source` must be nonempty strings. Optional `version` and
`effective_date`, when present, must also be nonempty strings. Unknown fields are
rejected by `parse_and_validate`. Required fields can be explicitly extended.
Date syntax and source authenticity are not validated by this experiment.

Valid JSON is parsed before attempting recovery. One missing closing delimiter
or one trailing comma at the end may be repaired, using structural delimiters
outside quoted strings. Complex malformed input and incomplete quoted strings
are rejected. Responses ending with a non-`stop` finish reason are not repaired
into successful observations.

JSON mode is requested with `response_format={"type":"json_object"}`. The schema
in the report describes local validation; it is not sent as a strict API schema.
Valid JSON alone does not establish factual correctness or source grounding.

## Reports and failure behavior

Default reports are `outputs/structured-results.json` and
`outputs/structured-results.md`. Use `--output` and `--markdown` to choose new paths.
Existing reports are never overwritten. JSON and Markdown paths must differ.

Reports distinguish attempts, API successes, and validation outcomes. Failed API
calls have no validation result; reports handle them explicitly. Provider error
types/statuses are retained without copying arbitrary error response text.
Any invalid response or failed call makes the live command exit nonzero after
saving available results. Nonpositive repetition counts are rejected.

The historical `outputs/sample_results.md` in this experiment directory is an
offline example, not measured API evidence. The regression tests cover quoted
braces, schema mismatches, request failures, truncation, and report preservation:

```bash
python -m pytest -q tests/test_structured_output.py
```
