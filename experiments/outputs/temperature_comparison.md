# Temperature Experiment

## Status

**EXPERIMENTS NOT RUN - Missing API Credentials**

This file is a placeholder. The temperature experiments require valid OpenAI API credentials to execute.

## To Run Experiments

1. Copy `.env.example` to `.env`
2. Fill in your `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `CHAT_MODEL`
3. Run: `python experiments/parameter_experiments.py`

## Expected Experiment Structure

Once run, this file will contain:

- **Prompt**: The consistent factual prompt used for all temperature tests
- **Temperature 0.0**: Deterministic output (should be identical across runs)
- **Temperature 0.3**: Low variation - consistent wording
- **Temperature 0.7**: Moderate variation - different phrasing
- **Temperature 1.0**: High variation - creative, diverse responses
- **Conclusion**: Analysis of temperature effects on response consistency

## Temperature Values to Test

- 0.0 (completely deterministic)
- 0.3 (low variation)
- 0.7 (moderate variation)
- 1.0 (high variation)

## Expected Observations

LOW TEMPERATURE (0.0-0.3):
- More stable, predictable, and consistent wording
- Suitable for factual, grounded responses
- Reduces unnecessary variation in answers

HIGHER TEMPERATURE (0.7-1.0):
- More variation in wording and structure
- Potentially more creative or diverse responses
- May introduce unnecessary variation for factual queries

IMPORTANT: Temperature does NOT guarantee factual correctness. Factuality primarily depends on retrieval quality, grounding, source quality, and prompt design.
