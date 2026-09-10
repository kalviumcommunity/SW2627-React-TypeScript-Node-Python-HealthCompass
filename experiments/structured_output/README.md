# Structured Output for RAG Assistant

## Overview

This experiment implements a reliable structured-output layer for the HealthCompass RAG assistant. Instead of allowing the LLM to return arbitrary prose, the model must return a defined JSON object with validated fields.

## Purpose

The structured output layer ensures:

1. **Predictable Response Format** - All responses follow a consistent JSON schema
2. **Required Field Validation** - Guarantees presence of essential information
3. **Malformed JSON Recovery** - Gracefully handles common JSON formatting errors
4. **Error Resilience** - Never crashes due to malformed model output
5. **Type Safety** - Validates data types and non-empty constraints

## JSON Schema

### Required Schema

```json
{
  "type": "object",
  "properties": {
    "answer": {
      "type": "string",
      "description": "A concise factual answer to the question"
    },
    "source": {
      "type": "string", 
      "description": "The name of the source document or repository"
    },
    "version": {
      "type": "string",
      "description": "Document version if applicable"
    },
    "effective_date": {
      "type": "string",
      "description": "Document effective date if applicable"
    }
  },
  "required": ["answer", "source"],
  "additionalProperties": false
}
```

### Required Fields

- **`answer`**: A concise factual answer to the question (non-empty string)
- **`source`**: The name of the source document or repository (non-empty string)

### Optional Fields

- **`version`**: Document version if applicable
- **`effective_date`**: Document effective date if applicable

## Project Structure

```
experiments/structured_output/
├── structured_output.py      # Main experiment runner with API integration
├── validator.py              # Parsing, validation, and recovery logic
├── outputs/
│   └── sample_results.md     # Test results and documentation
└── README.md                 # This file
```

## Components

### validator.py

Core validation and parsing logic:

- **`parse_structured_response()`** - Parses JSON with automatic recovery
- **`validate_required_fields()`** - Validates required fields and types
- **`parse_and_validate()`** - Complete parsing and validation pipeline
- **`attempt_json_recovery()`** - Safe recovery for common malformed patterns
- **`StructuredOutputResult`** - Result object with success/error information

### structured_output.py

Experiment runner for API testing:

- **`StructuredOutputRunner`** - Runs structured output experiments
- **`request_structured_output()`** - Makes API calls with JSON mode
- **`run_comparison()`** - Compares JSON mode vs regular mode
- **`save_results()`** - Saves experiment results to JSON
- **`generate_markdown_report()`** - Creates human-readable reports

## Recovery Mechanism

The validator implements safe, conservative JSON recovery for common malformed patterns:

### Supported Recovery Patterns

1. **Missing Closing Brace**
   - Input: `{"answer":"test","source":"test"`
   - Output: `{"answer":"test","source":"test"}`

2. **Missing Closing Bracket**
   - Input: `["answer","source"`
   - Output: `["answer","source"]`

3. **Trailing Comma Before Brace/Bracket**
   - Input: `{"answer":"test","source":"test",}`
   - Output: `{"answer":"test","source":"test"}`

### Safety Constraints

- Only recovers single missing braces/brackets (multiple missing = unsafe)
- Only recovers clear trailing comma patterns
- Does not attempt to fix arbitrary malformed JSON
- Returns original text if recovery is not safe

## Validation Rules

The validator enforces these rules:

1. **Type Check**: Response must be a JSON object (dictionary)
2. **Required Fields**: Both `answer` and `source` must be present
3. **Non-empty Strings**: Required fields must contain non-whitespace text
4. **String Type**: Required fields must be strings, not numbers or other types

## Usage

### Basic Validation

```python
from experiments.structured_output.validator import parse_and_validate

# Parse and validate a response
result = parse_and_validate('{"answer": "Test", "source": "Test"}')

if result.success:
    print(f"Valid: {result.data}")
else:
    print(f"Error: {result.error}")
```

### Running Experiments

```bash
# Dry run (no API calls)
python experiments/structured_output/structured_output.py --dry-run

# Live experiment with API calls
python experiments/structured_output/structured_output.py --repetitions 3

# Custom output paths
python experiments/structured_output/structured_output.py \
    --output custom_results.json \
    --markdown custom_report.md
```

### Integration with RAG Application

```python
from experiments.structured_output.validator import parse_and_validate
from openai import OpenAI

client = OpenAI(api_key="your-api-key")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Return JSON with answer and source fields"},
        {"role": "user", "content": "Your question here"}
    ],
    response_format={"type": "json_object"}
)

result = parse_and_validate(response.choices[0].message.content)

if result.success:
    answer = result.data["answer"]
    source = result.data["source"]
    # Use the structured data
else:
    # Handle validation error
    print(f"Validation failed: {result.error}")
```

## Testing

### Run Tests

```bash
# Run all structured output tests
pytest tests/test_structured_output.py -v

# Run specific test class
pytest tests/test_structured_output.py::TestValidateRequiredFields -v

# Run with coverage
pytest tests/test_structured_output.py --cov=experiments.structured_output
```

### Test Coverage

The test suite includes 32 tests covering:

- ✅ Valid JSON parsing
- ✅ Missing required field detection
- ✅ Empty field validation
- ✅ Wrong type validation
- ✅ Malformed JSON recovery
- ✅ Complete pipeline testing
- ✅ Error formatting
- ✅ Malformed-then-recovered case

## API Integration

### OpenAI JSON Mode

The experiment uses OpenAI's JSON mode for stronger guarantees:

```python
response = client.chat.completions.create(
    model=model,
    messages=messages,
    response_format={"type": "json_object"}  # Enables JSON mode
)
```

### System Prompt

The system prompt instructs the model to return JSON:

```
You are a factual RAG assistant for HealthCompass.

Return your response as valid JSON only.

The JSON must contain:
- answer: a concise factual answer to the question
- source: the name of the source document or repository

Do not include Markdown code fences.
Do not include explanatory text outside the JSON object.
```

## Error Handling

The parser never crashes due to malformed input:

### Empty Input
```python
result = parse_structured_response("")
# Result: success=False, error="Invalid input: response must be a non-empty string"
```

### Invalid JSON
```python
result = parse_structured_response('{"invalid": json}')
# Result: success=False, error="Invalid JSON response: ..."
```

### Missing Required Field
```python
result = parse_and_validate('{"answer": "test"}')
# Result: success=False, error="Missing required field: source"
```

### Wrong Type
```python
result = parse_and_validate('["answer", "source"]')
# Result: success=False, error="Expected JSON object, got list"
```

## Configuration

### Environment Variables

Required for live API testing:

```bash
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
CHAT_MODEL=gpt-4o-mini
```

### Experiment Parameters

- `--repetitions`: Number of repetitions per mode (default: 3)
- `--output`: Path for JSON results (default: experiments/structured_output/outputs/results.json)
- `--markdown`: Path for markdown report (default: experiments/structured_output/outputs/sample_results.md)
- `--dry-run`: Print plan without API calls

## Results

### Sample Results

See `experiments/structured_output/outputs/sample_results.md` for detailed test results including:

- All 6 required test cases with actual outputs
- Malformed-then-recovered case demonstration
- Additional recovery test cases
- Validation rule documentation
- Error handling examples

### Test Results Summary

- **Total Tests**: 32
- **Passed**: 32
- **Failed**: 0
- **Coverage**: All required scenarios including malformed JSON recovery

## Benefits

### For the RAG Application

1. **Consistency**: All responses follow the same structure
2. **Reliability**: Validation catches missing or malformed data
3. **Debugging**: Clear error messages for troubleshooting
4. **Safety**: Graceful handling of model errors
5. **Integration**: Easy to integrate with downstream systems

### For Users

1. **Predictable Format**: Always know what fields to expect
2. **Data Quality**: Validated fields ensure data integrity
3. **Error Transparency**: Clear messages when something goes wrong
4. **Robustness**: Application continues even with model errors

## Limitations

1. **Schema Fixed**: The JSON schema is currently fixed; dynamic schemas require additional implementation
2. **Recovery Scope**: Only handles common malformed patterns; complex errors may still fail
3. **API Dependency**: JSON mode support depends on the specific API provider
4. **Token Cost**: Structured output may require more tokens for complex responses

## Future Enhancements

1. **Dynamic Schema Support**: Allow custom JSON schemas per request
2. **Advanced Recovery**: More sophisticated JSON repair mechanisms
3. **Field Validation**: Add validation rules for optional fields (dates, versions)
4. **Batch Processing**: Support multiple structured outputs in one request
5. **Streaming**: Support streaming structured output responses

## Troubleshooting

### Common Issues

**Issue**: Validation fails with "Missing required field"
- **Solution**: Ensure both `answer` and `source` fields are present in the JSON

**Issue**: "Invalid JSON response" error
- **Solution**: Check if the model is returning valid JSON; enable JSON mode

**Issue**: Recovery not working
- **Solution**: Recovery only handles specific patterns; check if the malformed JSON matches supported patterns

**Issue**: API calls failing
- **Solution**: Verify environment variables are set correctly and API key is valid

## Contributing

When adding new validation rules or recovery patterns:

1. Add corresponding test cases in `tests/test_structured_output.py`
2. Update this README with new functionality
3. Ensure all existing tests pass
4. Update sample results if needed

## License

This is part of the HealthCompass RAG application project.
