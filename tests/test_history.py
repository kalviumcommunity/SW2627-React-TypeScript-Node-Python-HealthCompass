"""Regression coverage for complete turns, input budgets and request rollback."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app import ask_model, main
from healthcompass.chat.history import ConversationHistory, count_tokens, total_tokens, trim


def client_with(answer="answer"):
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=answer))]
    )
    return client


def test_estimate_handles_long_words_and_unicode():
    assert count_tokens("a" * 1000) == 1000
    assert count_tokens("हिन्दी") > len("हिन्दी")
    assert total_tokens([{"role": "system", "content": ""}]) > 0


def test_trim_whole_turns():
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "old answer"},
        {"role": "user", "content": "new"},
    ]
    trim(messages, 90)
    assert [m["role"] for m in messages] == ["system", "user"]
    assert messages[-1]["content"] == "new"


def test_oversized_prompt_is_rejected_without_mutation():
    history = ConversationHistory("s", budget=150, max_output_tokens=30)
    before = deepcopy(history.messages)
    with pytest.raises(ValueError, match="exceed"):
        history.add_user_message("x" * 150)
    assert history.messages == before


@pytest.mark.parametrize("budget,output", [(0, 1), (100, 100), (100, 0), (100, -1), (True, 1)])
def test_invalid_budgets(budget, output):
    with pytest.raises(ValueError):
        ConversationHistory("s", budget, output)


def test_system_prompt_must_fit():
    with pytest.raises(ValueError, match="exceed"):
        ConversationHistory("x" * 100, 100, 10)


def test_request_reserves_output_and_retains_follow_up(monkeypatch):
    monkeypatch.setenv("CHAT_MODEL", "test-model")
    history = ConversationHistory("s", 250, 40)
    client = client_with()
    ask_model(client, "first", history)
    ask_model(client, "follow up", history)
    request = client.chat.completions.create.call_args.kwargs
    assert [m["role"] for m in request["messages"]] == ["system", "user", "assistant", "user"]
    assert total_tokens(request["messages"]) + request["max_completion_tokens"] <= history.budget


def test_request_uses_grounded_generation_defaults(monkeypatch):
    monkeypatch.setenv("CHAT_MODEL", "test-model")
    history = ConversationHistory("s")
    client = client_with()
    ask_model(client, "question", history)
    request = client.chat.completions.create.call_args.kwargs
    assert request["temperature"] == 0.1
    assert request["max_completion_tokens"] == 300
    assert request["stop"] == ["\n\nUser:"]
    assert "top_p" not in request


def test_request_accepts_top_p_override(monkeypatch):
    monkeypatch.setenv("CHAT_MODEL", "test-model")
    history = ConversationHistory("s", top_p=0.5, stop=["END_OF_ANSWER"])
    client = client_with()
    ask_model(client, "question", history)
    request = client.chat.completions.create.call_args.kwargs
    assert request["top_p"] == 0.5
    assert request["stop"] == ["END_OF_ANSWER"]


def test_failed_request_restores_previous_turns(monkeypatch):
    monkeypatch.setenv("CHAT_MODEL", "test-model")
    history = ConversationHistory("s", 180, 40)
    client = client_with()
    ask_model(client, "first", history)
    before = deepcopy(history.messages)
    client.chat.completions.create.side_effect = RuntimeError("offline")
    with pytest.raises(RuntimeError):
        ask_model(client, "next " * 9, history)
    assert history.messages == before


def test_empty_response_rolls_back(monkeypatch):
    monkeypatch.setenv("CHAT_MODEL", "test-model")
    history = ConversationHistory("s")
    with pytest.raises(ValueError, match="no usable text"):
        ask_model(client_with(None), "question", history)
    assert len(history.messages) == 1


def test_interactive_cli_reuses_history(monkeypatch):
    import app

    client = client_with()
    monkeypatch.setenv("CHAT_MODEL", "test-model")
    monkeypatch.setattr(app, "validate_env", lambda: None)
    monkeypatch.setattr(app, "create_client", lambda: client)
    inputs = iter(["first", "second", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr("sys.argv", ["app", "--chat"])
    assert main() == 0
    assert len(client.chat.completions.create.call_args.kwargs["messages"]) == 4


def test_compare_uses_independent_histories_and_configured_cap(monkeypatch):
    from app import compare_prompts

    monkeypatch.setenv("CHAT_MODEL", "test-model")
    client = client_with()
    compare_prompts(client, budget=1500, max_output_tokens=60, token_limit_parameter="max_tokens")
    requests = client.chat.completions.create.call_args_list
    assert len(requests) == 2
    for call in requests:
        assert [message["role"] for message in call.kwargs["messages"]] == ["system", "user"]
        assert call.kwargs["max_tokens"] == 60
        assert "max_completion_tokens" not in call.kwargs


def test_cli_configuration_errors_use_stderr(monkeypatch, capsys):
    import app

    def invalid_configuration():
        raise RuntimeError("Missing configuration")

    monkeypatch.setattr(app, "validate_env", invalid_configuration)
    monkeypatch.setattr("sys.argv", ["app"])
    assert main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Missing configuration" in captured.err


def test_invalid_role_sequence_does_not_mutate_history():
    messages = [{"role": "system", "content": "s"}, {"role": "assistant", "content": "a"}]
    previous = deepcopy(messages)
    with pytest.raises(ValueError, match="alternate"):
        trim(messages)
    assert messages == previous
