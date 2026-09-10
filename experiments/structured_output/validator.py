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
        recovery_attempted: bool = False
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
            "recovery_attempted": self.recovery_attempted
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
            raw_input=response_text
        )
    
    # Attempt to recover common malformed JSON patterns
    recovered_text = attempt_json_recovery(response_text)
    recovery_attempted = recovered_text != response_text
    
    try:
        parsed = json.loads(recovered_text)
        return StructuredOutputResult(
            success=True,
            data=parsed,
            raw_input=response_text,
            recovery_attempted=recovery_attempted
        )
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON response: {str(e)}"
        if recovery_attempted:
            error_msg += " (recovery attempted but failed)"
        return StructuredOutputResult(
            success=False,
            error=error_msg,
            raw_input=response_text,
            recovery_attempted=recovery_attempted
        )


def attempt_json_recovery(response_text: str) -> str:
    """
    Attempt to recover from common malformed JSON patterns.
    
    This function only attempts safe, conservative repairs where the intent
    is unambiguous. It does not try to fix arbitrary malformed JSON.
    
    Recovery patterns handled:
    - Missing closing brace (single brace only)
    - Missing closing bracket (single bracket only)
    - Trailing comma before closing brace/bracket
    
    Args:
        response_text: Potentially malformed JSON text
        
    Returns:
        Recovered JSON text if safe recovery possible, otherwise original text
    """
    text = response_text.strip()
    original = text
    
    # Pattern 3: Trailing comma before closing brace/bracket (handle first)
    text = text.rstrip()
    # Check for patterns like ",}" or ",]"
    if (text.endswith(",}") or text.endswith(",]")):
        # Remove the trailing comma
        text = text[:-2] + text[-1]
    
    # Pattern 1: Missing closing brace (only single missing brace)
    open_braces = text.count("{")
    close_braces = text.count("}")
    if open_braces > close_braces and open_braces - close_braces == 1:
        # Check if the text ends with a valid JSON value (not incomplete)
        if not text.endswith(",") and not text.endswith(":"):
            text += "}"
    
    # Pattern 2: Missing closing bracket (only single missing bracket)
    open_brackets = text.count("[")
    close_brackets = text.count("]")
    if open_brackets > close_brackets and open_brackets - close_brackets == 1:
        if not text.endswith(",") and not text.endswith(":"):
            text += "]"
    
    # If no recovery was possible, return original
    if text == original:
        return original
    
    return text


def validate_required_fields(
    data: Dict[str, Any],
    required_fields: list[str] = None
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
            success=False,
            error=f"Expected JSON object, got {type(data).__name__}",
            data=data
        )
    
    # Check each required field
    for field in required_fields:
        if field not in data:
            return StructuredOutputResult(
                success=False,
                error=f"Missing required field: {field}",
                data=data
            )
        
        value = data[field]
        if not isinstance(value, str):
            return StructuredOutputResult(
                success=False,
                error=f"Field '{field}' must be a string, got {type(value).__name__}",
                data=data
            )
        
        if not value.strip():
            return StructuredOutputResult(
                success=False,
                error=f"Field '{field}' cannot be empty",
                data=data
            )
    
    return StructuredOutputResult(
        success=True,
        data=data
    )


def parse_and_validate(
    response_text: str,
    required_fields: list[str] = None
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
    
    # Combine results
    return StructuredOutputResult(
        success=validation_result.success,
        data=validation_result.data,
        error=validation_result.error,
        raw_input=response_text,
        recovery_attempted=parse_result.recovery_attempted
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
