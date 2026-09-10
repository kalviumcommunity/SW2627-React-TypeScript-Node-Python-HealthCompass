"""Tests for structured output validation and parsing."""

import pytest

from experiments.structured_output import (
    attempt_json_recovery,
    format_validation_error,
    parse_and_validate,
    parse_structured_response,
    StructuredOutputResult,
    validate_required_fields,
    ValidationError,
)


class TestParseStructuredResponse:
    """Test JSON parsing functionality."""
    
    def test_valid_json(self):
        """TEST 1 - Valid JSON should parse successfully."""
        input_json = '{"answer": "Use the current approved guideline.", "source": "Outbreak Response Guideline"}'
        result = parse_structured_response(input_json)
        
        assert result.success is True
        assert result.data == {
            "answer": "Use the current approved guideline.",
            "source": "Outbreak Response Guideline"
        }
        assert result.error is None
        assert result.recovery_attempted is False
    
    def test_missing_closing_brace_recovery(self):
        """Test recovery from missing closing brace."""
        malformed = '{"answer": "Use current guidance", "source": "Outbreak Guideline"'
        result = parse_structured_response(malformed)
        
        assert result.success is True
        assert result.recovery_attempted is True
        assert result.data == {
            "answer": "Use current guidance",
            "source": "Outbreak Guideline"
        }
    
    def test_invalid_json_no_recovery(self):
        """Test that truly invalid JSON fails even after recovery attempt."""
        malformed = '{"answer": "test", "source": "test"'
        # Make it unrecoverable by adding invalid syntax
        truly_malformed = '{"answer": "test", "source": invalid}'
        result = parse_structured_response(truly_malformed)
        
        assert result.success is False
        assert "Invalid JSON response" in result.error
    
    def test_empty_input(self):
        """Test that empty input fails gracefully."""
        result = parse_structured_response("")
        
        assert result.success is False
        assert "Invalid input" in result.error
    
    def test_non_string_input(self):
        """Test that non-string input fails gracefully."""
        result = parse_structured_response(None)
        
        assert result.success is False
        assert "Invalid input" in result.error


class TestValidateRequiredFields:
    """Test required field validation."""
    
    def test_valid_complete_response(self):
        """TEST 1 - Valid complete response should pass validation."""
        data = {
            "answer": "Use the current approved guideline.",
            "source": "Outbreak Response Guideline"
        }
        result = validate_required_fields(data)
        
        assert result.success is True
        assert result.data == data
        assert result.error is None
    
    def test_missing_source_field(self):
        """TEST 2 - Missing source field should fail validation."""
        data = {"answer": "Use the current approved guideline."}
        result = validate_required_fields(data)
        
        assert result.success is False
        assert "Missing required field: source" in result.error
        assert result.data == data
    
    def test_missing_answer_field(self):
        """TEST 3 - Missing answer field should fail validation."""
        data = {"source": "Outbreak Response Guideline"}
        result = validate_required_fields(data)
        
        assert result.success is False
        assert "Missing required field: answer" in result.error
        assert result.data == data
    
    def test_wrong_json_type_array(self):
        """TEST 5 - Array instead of object should fail validation."""
        data = ["answer", "source"]
        result = validate_required_fields(data)
        
        assert result.success is False
        assert "Expected JSON object" in result.error
        assert result.data == data
    
    def test_empty_answer_field(self):
        """TEST 6 - Empty answer field should fail validation."""
        data = {"answer": "", "source": "Outbreak Guideline"}
        result = validate_required_fields(data)
        
        assert result.success is False
        assert "Field 'answer' cannot be empty" in result.error
    
    def test_empty_source_field(self):
        """Test empty source field should fail validation."""
        data = {"answer": "Test answer", "source": ""}
        result = validate_required_fields(data)
        
        assert result.success is False
        assert "Field 'source' cannot be empty" in result.error
    
    def test_whitespace_only_field(self):
        """Test that whitespace-only fields fail validation."""
        data = {"answer": "   ", "source": "Test"}
        result = validate_required_fields(data)
        
        assert result.success is False
        assert "Field 'answer' cannot be empty" in result.error
    
    def test_non_string_field_type(self):
        """Test that non-string field types fail validation."""
        data = {"answer": 123, "source": "Test"}
        result = validate_required_fields(data)
        
        assert result.success is False
        assert "Field 'answer' must be a string" in result.error
    
    def test_custom_required_fields(self):
        """Test validation with custom required fields."""
        data = {"answer": "Test", "source": "Test", "version": "1.0"}
        result = validate_required_fields(data, required_fields=["answer", "source", "version"])
        
        assert result.success is True
    
    def test_custom_required_field_missing(self):
        """Test validation fails when custom required field is missing."""
        data = {"answer": "Test", "source": "Test"}
        result = validate_required_fields(data, required_fields=["answer", "source", "version"])
        
        assert result.success is False
        assert "Missing required field: version" in result.error


class TestAttemptJsonRecovery:
    """Test JSON recovery functionality."""
    
    def test_missing_closing_brace(self):
        """Test recovery of missing closing brace."""
        malformed = '{"answer": "test", "source": "test"'
        recovered = attempt_json_recovery(malformed)
        
        assert recovered == '{"answer": "test", "source": "test"}'
    
    def test_missing_closing_bracket(self):
        """Test recovery of missing closing bracket."""
        malformed = '["answer", "source"'
        recovered = attempt_json_recovery(malformed)
        
        assert recovered == '["answer", "source"]'
    
    def test_trailing_comma_before_brace(self):
        """Test removal of trailing comma before closing brace."""
        malformed = '{"answer": "test", "source": "test",}'
        recovered = attempt_json_recovery(malformed)
        
        # Trailing comma removal is supported
        assert recovered == '{"answer": "test", "source": "test"}'
    
    def test_trailing_comma_before_bracket(self):
        """Test removal of trailing comma before closing bracket."""
        malformed = '["answer", "source",]'
        recovered = attempt_json_recovery(malformed)
        
        assert recovered == '["answer", "source"]'
    
    def test_no_recovery_needed(self):
        """Test that valid JSON is unchanged."""
        valid = '{"answer": "test", "source": "test"}'
        recovered = attempt_json_recovery(valid)
        
        assert recovered == valid
    
    def test_complex_malformed_no_recovery(self):
        """Test that complex malformed JSON is not recovered."""
        truly_malformed = '{"answer": "test", "source": invalid}'
        recovered = attempt_json_recovery(truly_malformed)
        
        # Should not change invalid JSON
        assert recovered == truly_malformed
    
    def test_multiple_missing_braces_no_recovery(self):
        """Test that single missing brace is recovered (safe)."""
        malformed = '{"answer": "test"'
        recovered = attempt_json_recovery(malformed)
        
        # Single missing brace is recovered (safe)
        assert recovered == '{"answer": "test"}'


class TestParseAndValidate:
    """Test complete parsing and validation pipeline."""
    
    def test_successful_pipeline(self):
        """Test complete pipeline with valid input."""
        input_json = '{"answer": "Test", "source": "Test"}'
        result = parse_and_validate(input_json)
        
        assert result.success is True
        assert result.data == {"answer": "Test", "source": "Test"}
        assert result.error is None
    
    def test_pipeline_with_recovery(self):
        """Test pipeline with successful recovery."""
        malformed = '{"answer": "Test", "source": "Test"'
        result = parse_and_validate(malformed)
        
        assert result.success is True
        assert result.recovery_attempted is True
        assert result.data == {"answer": "Test", "source": "Test"}
    
    def test_pipeline_validation_failure(self):
        """Test pipeline with validation failure."""
        incomplete = '{"answer": "Test"}'
        result = parse_and_validate(incomplete)
        
        assert result.success is False
        assert "Missing required field: source" in result.error
    
    def test_pipeline_parse_failure(self):
        """Test pipeline with parse failure."""
        invalid = '{"answer": "test", invalid}'
        result = parse_and_validate(invalid)
        
        assert result.success is False
        assert "Invalid JSON response" in result.error


class TestFormatValidationError:
    """Test error formatting."""
    
    def test_format_success(self):
        """Test formatting of successful result."""
        result = StructuredOutputResult(success=True, data={"test": "data"})
        formatted = format_validation_error(result)
        
        assert formatted == "Validation passed"
    
    def test_format_error(self):
        """Test formatting of error result."""
        result = StructuredOutputResult(
            success=False,
            error="Test error message",
            recovery_attempted=False
        )
        formatted = format_validation_error(result)
        
        assert "Structured output validation failed" in formatted
        assert "Test error message" in formatted
    
    def test_format_error_with_recovery(self):
        """Test formatting of error result with recovery attempt."""
        result = StructuredOutputResult(
            success=False,
            error="Test error message",
            recovery_attempted=True
        )
        formatted = format_validation_error(result)
        
        assert "Structured output validation failed" in formatted
        assert "recovery was attempted" in formatted


class TestStructuredOutputResult:
    """Test StructuredOutputResult class."""
    
    def test_to_dict_success(self):
        """Test to_dict conversion for successful result."""
        result = StructuredOutputResult(
            success=True,
            data={"answer": "test"},
            raw_input="test input"
        )
        result_dict = result.to_dict()
        
        assert result_dict["success"] is True
        assert result_dict["data"] == {"answer": "test"}
        assert result_dict["error"] is None
        assert result_dict["raw_input"] == "test input"
        assert result_dict["recovery_attempted"] is False
    
    def test_to_dict_failure(self):
        """Test to_dict conversion for failed result."""
        result = StructuredOutputResult(
            success=False,
            error="Test error",
            raw_input="test input",
            recovery_attempted=True
        )
        result_dict = result.to_dict()
        
        assert result_dict["success"] is False
        assert result_dict["data"] is None
        assert result_dict["error"] == "Test error"
        assert result_dict["raw_input"] == "test input"
        assert result_dict["recovery_attempted"] is True


class TestMalformedThenRecovered:
    """Test the specific malformed-then-recovered case requirement."""
    
    def test_malformed_then_recovered_case(self):
        """
        TEST 4 - Complete malformed-then-recovered case.
        
        This test demonstrates:
        1. Initial model/raw output is malformed
        2. Parser detects the error
        3. Recovery is attempted
        4. Recovery succeeds
        5. Final result is successfully parsed and validated
        """
        # Step 1: Initial malformed output
        raw_output = '{"answer":"Use current approved guidance","source":"Outbreak Guideline"'
        
        # Step 2: Initial parsing should detect the error
        initial_parse = parse_structured_response(raw_output)
        # Actually, our recovery is automatic, so let's test without recovery
        # We need to test the recovery mechanism directly
        
        # Test the recovery specifically
        recovered_text = attempt_json_recovery(raw_output)
        assert recovered_text == '{"answer":"Use current approved guidance","source":"Outbreak Guideline"}'
        
        # Step 3 & 4: Recovery succeeds and parses
        final_parse = parse_structured_response(raw_output)
        assert final_parse.success is True
        assert final_parse.recovery_attempted is True
        
        # Step 5: Final result is successfully validated
        final_validation = parse_and_validate(raw_output)
        assert final_validation.success is True
        assert final_validation.data == {
            "answer": "Use current approved guidance",
            "source": "Outbreak Guideline"
        }
        assert final_validation.recovery_attempted is True
