# Top P Experiment

## Status

**EXPERIMENTS NOT RUN - Missing API Credentials**

This file is a placeholder. The top_p experiments require valid OpenAI API credentials to execute.

## To Run Experiments

1. Copy `.env.example` to `.env`
2. Fill in your `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `CHAT_MODEL`
3. Run: `python experiments/parameter_experiments.py`

## Expected Experiment Structure

Once run, this file will contain:

- **Prompt**: The consistent factual prompt
- **Fixed temperature**: 0.3 (to isolate top_p effects)
- **top_p = 0.1**: Highly constrained generation
- **top_p = 0.5**: Moderate constraint
- **top_p = 1.0**: No nucleus sampling constraint (default)
- **Conclusion**: Analysis of top_p effects on generation focus

## Top P Values to Test

- 0.1 (highly constrained)
- 0.5 (moderate constraint)
- 1.0 (no constraint - default)

## Expected Observations

top_p controls nucleus sampling by restricting token selection to a probability mass.

Lower top_p (e.g., 0.1):
- More constrained generation
- Only considers most likely tokens
- More focused, predictable output

Medium top_p (e.g., 0.5):
- Moderate constraint
- Balances focus and diversity

top_p = 1.0:
- No nucleus sampling constraint
- Considers all tokens in probability distribution
- Standard default behavior

For grounded RAG, keeping top_p at default (1.0) and using temperature as the primary tuning parameter is generally recommended.
