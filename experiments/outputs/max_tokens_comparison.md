# Max Tokens Experiment

## Status

**EXPERIMENTS NOT RUN - Missing API Credentials**

This file is a placeholder. The max_tokens experiments require valid OpenAI API credentials to execute.

## To Run Experiments

1. Copy `.env.example` to `.env`
2. Fill in your `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `CHAT_MODEL`
3. Run: `python experiments/parameter_experiments.py`

## Expected Experiment Structure

Once run, this file will contain:

- **Prompt**: A longer prompt designed to generate extended responses
- **max_tokens = 20**: Very short answer, likely truncated
- **max_tokens = 50**: Moderate length answer
- **max_tokens = 150**: Complete answer with full explanation
- **Conclusion**: Analysis of how max_tokens affects response completeness

## Max Tokens Values to Test

- 20 (very short)
- 50 (moderate)
- 150 (complete)

## Expected Observations

Small max_tokens (e.g., 20):
- Very short answers, likely truncated
- May cut off important information

Medium max_tokens (e.g., 50):
- Moderate length answers
- May still truncate for complex responses

Larger max_tokens (e.g., 150+):
- More complete answers
- Allows for full explanation

max_tokens controls the maximum amount of generated output, helping control response length and generation cost.
