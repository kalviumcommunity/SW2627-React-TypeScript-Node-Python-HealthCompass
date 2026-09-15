"""Structured output validation and parsing for RAG assistant responses."""

import json
from typing import Any, Dict, Optional


class ValidationError(Exception):
    """Raised when structured output validation fails."""

    pass


class StructuredOutputResult:
    """Result of parsing and validating structured output."""

    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        raw_input: Optional[str] = None,
        recovery_attempted: bool = False,
    ):
        self.success = success
        self.data = data
        self.error = error
        self.raw_input = raw_input
        self.recovery_attempted = recovery_attempted

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "raw_input": self.raw_input,
            "recovery_attempted": self.recovery_attempted,
        }


def parse_structured_response(response_text: str) -> StructuredOutputResult:
    """
    Parse a structured JSON response from the model.

    Args:
        response_text: Raw text response from the model

    Returns:
        StructuredOutputResult with parsed data or error information
    """
    if not response_text or not isinstance(response_text, str):
        return StructuredOutputResult(
            success=False,
            error="Invalid input: response must be a non-empty string",
            raw_input=response_text,
        )

    try:
        parsed = json.loads(response_text)
        return StructuredOutputResult(success=True, data=parsed, raw_input=response_text)
    except json.JSONDecodeError:
        pass
    recovered_text = attempt_json_recovery(response_text)
    try:
        return StructuredOutputResult(
            success=True,
            data=json.loads(recovered_text),
            raw_input=response_text,
            recovery_attempted=recovered_text != response_text,
        )
    except json.JSONDecodeError as exc:
        return StructuredOutputResult(
            success=False,
            error=f"Invalid JSON response: {exc}",
            raw_input=response_text,
            recovery_attempted=recovered_text != response_text,
        )


def attempt_json_recovery(response_text: str) -> str:
    """Try one structural repair, never count delimiters inside JSON strings."""
    try:
        json.loads(response_text)
        return response_text
    except json.JSONDecodeError:
        pass
    text = response_text.strip()
    stack = []
    punctuation = []
    in_string = escaped = False
    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "{[":
            stack.append(char)
        elif char in "}]":
            if not stack or stack.pop() != {"}": "{", "]": "["}[char]:
                return response_text
        if not char.isspace():
            punctuation.append((index, char))
    if in_string:
        return response_text
    candidate = text
    if len(stack) == 1 and text and text[-1] not in ",:":
        candidate += {"{": "}", "[": "]"}[stack[0]]
    elif not stack and len(punctuation) >= 2:
        (position, previous), (_, last) = punctuation[-2:]
        if previous == "," and last in "}]":
            candidate = text[:position] + text[position + 1 :]
    try:
        json.loads(candidate)
        return candidate
    except json.JSONDecodeError:
        return response_text


def validate_required_fields(
    data: Dict[str, Any], required_fields: list[str] = None
) -> StructuredOutputResult:
    """
    Validate that required fields exist and are non-empty strings.

    Args:
        data: Parsed JSON data as dictionary
        required_fields: List of required field names (default: ["answer", "source"])

    Returns:
        StructuredOutputResult with validation result
    """
    if required_fields is None:
        required_fields = ["answer", "source"]

    # Check if data is a dictionary
    if not isinstance(data, dict):
        return StructuredOutputResult(
            success=False, error=f"Expected JSON object, got {type(data).__name__}", data=data
        )

    # Check each required field
    for field in required_fields:
        if field not in data:
            return StructuredOutputResult(
                success=False, error=f"Missing required field: {field}", data=data
            )

        value = data[field]
        if not isinstance(value, str):
            return StructuredOutputResult(
                success=False,
                error=f"Field '{field}' must be a string, got {type(value).__name__}",
                data=data,
            )

        if not value.strip():
            return StructuredOutputResult(
                success=False, error=f"Field '{field}' cannot be empty", data=data
            )

    return StructuredOutputResult(success=True, data=data)


def parse_and_validate(
    response_text: str, required_fields: list[str] = None
) -> StructuredOutputResult:
    """
    Complete pipeline: parse JSON response and validate required fields.

    Args:
        response_text: Raw text response from the model
        required_fields: List of required field names (default: ["answer", "source"])

    Returns:
        StructuredOutputResult with final validation result
    """
    # Step 1: Parse JSON
    parse_result = parse_structured_response(response_text)
    if not parse_result.success:
        return parse_result

    # Step 2: Validate required fields
    validation_result = validate_required_fields(parse_result.data, required_fields)

    if validation_result.success:
        allowed = {"answer", "source", "version", "effective_date"} | set(required_fields or [])
        for field, value in parse_result.data.items():
            if field not in allowed:
                validation_result = StructuredOutputResult(
                    success=False, data=parse_result.data, error=f"Unexpected field: {field}"
                )
                break
            if not isinstance(value, str) or not value.strip():
                validation_result = StructuredOutputResult(
                    success=False,
                    data=parse_result.data,
                    error=f"Field '{field}' must be a nonempty string",
                )
                break

    # Combine results
    return StructuredOutputResult(
        success=validation_result.success,
        data=validation_result.data,
        error=validation_result.error,
        raw_input=response_text,
        recovery_attempted=parse_result.recovery_attempted,
    )


def format_validation_error(result: StructuredOutputResult) -> str:
    """
    Format a validation error for display.

    Args:
        result: StructuredOutputResult with error

    Returns:
        Formatted error message
    """
    if result.success:
        return "Validation passed"

    error_msg = f"Structured output validation failed: {result.error}"
    if result.recovery_attempted:
        error_msg += " (recovery was attempted)"
    return error_msg
