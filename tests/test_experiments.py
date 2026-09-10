"""Offline tests verify experiment mechanics, not model quality."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
from openai import APIConnectionError
import pytest

from experiments.parameter_experiments import (
    ExperimentRunner, experiment_cases, main, summarize, write_report,
)


def response(content="answer", finish_reason="stop", usage=True):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason=finish_reason)],
        model="test-model", system_fingerprint="test-fingerprint",
        usage=SimpleNamespace(model_dump=lambda: {"completion_tokens": 10, "prompt_tokens": 20,
                                                 "total_tokens": 30}) if usage else None,
    )


def test_plan_varies_one_control_with_repetitions():
    cases = experiment_cases()
    assert len(cases) == 36
    for parameter in {c["parameter"] for c in cases}:
        group = [c for c in cases if c["parameter"] == parameter]
        varied = "max_completion_tokens" if parameter == "output_limit" else parameter
        fixed = [{k: v for k, v in c["settings"].items() if k != varied} for c in group]
        assert all(settings == fixed[0] for settings in fixed)
        assert {c["run"] for c in group} == {1, 2, 3}
    assert all("temperature" not in c["settings"] for c in cases if c["parameter"] == "top_p")
    assert any(c["settings"].get("stop") == ["END_OF_ANSWER"] for c in cases)


def test_success_failure_and_null_content_are_reported(tmp_path):
    client = Mock()
    client.chat.completions.create.side_effect = [
        response("first", "length"), response("second", usage=False),
        APIConnectionError(request=httpx.Request("POST", "https://example.invalid")), response(None),
    ]
    cases = [experiment_cases()[0]] * 4
    records = ExperimentRunner(client, "test-model").run(cases)
    summary = summarize(records)
    assert (summary["attempted"], summary["successful"], summary["failed"]) == (4, 2, 2)
    metric = summary["comparisons"][0]
    assert metric["distinct_outputs"] == 2
    assert metric["length_limited"] == 1
    assert metric["mean_completion_tokens"] == 10
    assert metric["usage_samples"] == 1
    path = tmp_path / "results.json"
    write_report(path, records)
    assert json.loads(path.read_text())["records"][1]["usage"] is None
    with pytest.raises(FileExistsError):
        write_report(path, records)


def test_dry_run_needs_no_credentials(monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert main(["--dry-run"]) == 0
    assert json.loads(capsys.readouterr().out)["planned_calls"] == 36


def test_live_failures_exit_nonzero(monkeypatch, tmp_path):
    import experiments.parameter_experiments as module
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setenv("CHAT_MODEL", "test-model")
    client = Mock()
    client.chat.completions.create.side_effect = APIConnectionError(
        request=httpx.Request("POST", "https://example.invalid"))
    factory = Mock()
    factory.return_value.__enter__ = Mock(return_value=client)
    factory.return_value.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(module, "OpenAI", factory)
    path = tmp_path / "failed.json"
    assert main(["--output", str(path), "--repetitions", "2"]) == 1
    summary = json.loads(path.read_text())["summary"]
    assert summary["failed"] == summary["attempted"] == 24
    assert summary["successful"] == 0
    assert factory.call_args.kwargs["max_retries"] == 0


def test_no_data_has_no_variation_claim():
    record = {**experiment_cases()[0], "status": "error"}
    assert summarize([record])["comparisons"][0]["distinct_outputs"] is None


def test_repetition_validation():
    with pytest.raises(ValueError):
        experiment_cases(1)
