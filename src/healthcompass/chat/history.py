"""Bounded text-only conversation history with atomic turn updates."""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI
import os

SYSTEM_PROMPT = (
    "You are a support assistant for an internal docs tool. "
    "Answer in two sentences maximum. If you are unsure, say you don't know."
)
DEFAULT_CONTEXT_BUDGET = 6000
DEFAULT_OUTPUT_TOKENS = 300
DEFAULT_TEMPERATURE = 0.1
DEFAULT_STOP = ["\n\nUser:"]


def count_tokens(text: str) -> int:
    """Conservative UTF-8 byte estimate, not a model tokenizer or billing count."""
    return len(text.encode("utf-8"))


def total_tokens(messages: list[dict[str, str]]) -> int:
    """Include a conservative framing allowance for simple role/content messages.

    Provider-specific tokenization/framing can differ. Configure a budget below
    the model's actual context limit; tools and multimodal content are unsupported.
    """
    return 16 + sum(
        16 + count_tokens(message["role"]) + count_tokens(message["content"])
        for message in messages
    )


def trim(messages: MutableSequence[dict[str, str]], budget: int = DEFAULT_CONTEXT_BUDGET) -> None:
    """Remove complete oldest turns; preserve system and newest turn or fail atomically."""
    if type(budget) is not int or budget < 1:
        raise ValueError("budget must be a positive integer")
    candidate = list(messages)
    if not candidate or candidate[0]["role"] != "system":
        raise ValueError("History must start with a system message")
    for index, message in enumerate(candidate[1:]):
        expected = "user" if index % 2 == 0 else "assistant"
        if message["role"] != expected:
            raise ValueError("History must alternate user and assistant messages")
    while total_tokens(candidate) > budget:
        # Keep the latest user message (and its response, when present).
        if len(candidate) <= 3:
            raise ValueError("System and newest turn exceed the context budget; shorten the input")
        del candidate[1:3]
    messages[:] = candidate


class ConversationHistory:
    """Maintain valid turns and reserve output space before each request."""

    def __init__(
        self,
        system_prompt: str = SYSTEM_PROMPT,
        budget: int = DEFAULT_CONTEXT_BUDGET,
        max_output_tokens: int = DEFAULT_OUTPUT_TOKENS,
        token_limit_parameter: str = "max_completion_tokens",
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float | None = None,
        stop: list[str] | None = None,
    ) -> None:
        if type(budget) is not int or type(max_output_tokens) is not int:
            raise ValueError("Context and output budgets must be integers")
        if max_output_tokens < 1 or budget <= max_output_tokens:
            raise ValueError("Context budget must exceed the positive output budget")
        if token_limit_parameter not in {"max_completion_tokens", "max_tokens"}:
            raise ValueError("Unsupported token limit parameter")
        if type(temperature) not in {int, float} or not 0 <= temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        if top_p is not None and (type(top_p) not in {int, float} or not 0 <= top_p <= 1):
            raise ValueError("top_p must be between 0 and 1")
        if stop is not None and (not stop or any(not item for item in stop)):
            raise ValueError("stop must contain non-empty sequences")
        self.budget = budget
        self.max_output_tokens = max_output_tokens
        self.token_limit_parameter = token_limit_parameter
        self.temperature = temperature
        self.top_p = top_p
        self.stop = list(DEFAULT_STOP if stop is None else stop)
        self.messages = [{"role": "system", "content": system_prompt}]
        trim(self.messages, self.input_budget)

    @property
    def input_budget(self) -> int:
        return self.budget - self.max_output_tokens

    def add_user_message(self, prompt: str) -> None:
        if not prompt.strip():
            raise ValueError("Prompt must not be blank")
        candidate = self.messages + [{"role": "user", "content": prompt}]
        trim(candidate, self.input_budget)
        self.messages = candidate

    def add_assistant_message(self, response: str) -> None:
        if not response.strip():
            raise ValueError("Model returned no usable text")
        candidate = self.messages + [{"role": "assistant", "content": response}]
        trim(candidate, self.budget)
        self.messages = candidate

    def ask(self, client: OpenAI) -> str:
        if self.messages[-1]["role"] != "user":
            raise ValueError("Add a user message before requesting a response")
        candidate = [message.copy() for message in self.messages]
        trim(candidate, self.input_budget)
        response = client.chat.completions.create(
            model=os.environ["CHAT_MODEL"],
            messages=candidate,
            temperature=self.temperature,
            **{self.token_limit_parameter: self.max_output_tokens},
            stop=self.stop,
            **({"top_p": self.top_p} if self.top_p is not None else {}),
        )
        if not response.choices:
            raise ValueError("Model returned no choices")
        answer = response.choices[0].message.content or ""
        self.add_assistant_message(answer)
        return answer
