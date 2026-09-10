# All Parameter Experiment Results

## Status

**EXPERIMENTS NOT RUN - Missing API Credentials**

This file is a placeholder. All experiments require valid OpenAI API credentials to execute.

## To Run Experiments

1. Copy `.env.example` to `.env`
2. Fill in your `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `CHAT_MODEL`
3. Run: `python experiments/parameter_experiments.py`

## Expected Experiment Summary

Once run, this file will contain:

- **Model**: The chat model used for experiments
- **Total API Calls**: Number of API requests made (expected: 10)
- **Experiment Date**: Timestamp of experiment execution
- **Temperature Results**: All temperature experiment outputs
- **Max Tokens Results**: All max_tokens experiment outputs
- **Top P Results**: All top_p experiment outputs

## Experiment Configuration

### Temperature Experiment
- Values: 0.0, 0.3, 0.7, 1.0
- Runs per value: 1
- Total API calls: 4

### Max Tokens Experiment
- Values: 20, 50, 150
- Runs per value: 1
- Total API calls: 3

### Top P Experiment
- Values: 0.1, 0.5, 1.0
- Fixed temperature: 0.3
- Runs per value: 1
- Total API calls: 3

**Total Expected API Calls: 10**

## Notes

This consolidated view allows easy comparison of all parameter effects in one document.
