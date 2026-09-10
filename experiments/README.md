# LLM Parameter Experiments for Grounded RAG

## Purpose

This experiment suite evaluates LLM generation parameters for a factual, grounded RAG assistant serving public health guidance. The experiments demonstrate how different generation parameters affect response consistency, length, and variability.

## Experiment Setup

The experiments use the OpenAI Chat Completions API with a consistent factual prompt about why RAG assistants should prioritize current and approved guidance over older document versions.

**Base Prompt:**
```
Answer the following question using ONLY the provided context.

Context:
The HealthCompass public-health guidance repository contains official documents with version numbers, effective dates, geographic applicability, and approval status. Active and approved guidance should be preferred over superseded or expired guidance.

Question:
Why should a RAG assistant prioritize current and approved guidance instead of relying on an older document version?

Give a concise factual explanation.
```

## Running the Experiments

To run the experiments:

1. Ensure you have valid OpenAI API credentials
2. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   copy .env.example .env
   ```
3. Activate the virtual environment:
   ```bash
   .\.venv\Scripts\Activate.ps1
   ```
4. Run the experiment script:
   ```bash
   python experiments/parameter_experiments.py
   ```

The script will:
- Test temperature values: 0.0, 0.3, 0.7, 1.0
- Test max_tokens values: 20, 50, 150
- Test top_p values: 0.1, 0.5, 1.0
- Save results to `experiments/outputs/`

## Temperature

### What it does
Temperature controls the randomness in token selection. Lower temperatures make the model more deterministic, while higher temperatures increase randomness and variety.

### Experiment Results
**Note:** Actual experiment results require API credentials to run. The script is ready to execute once credentials are configured.

Expected observations:
- **Temperature 0.0**: Completely deterministic - identical responses on repeated runs
- **Temperature 0.3**: Low variation - consistent wording with minor differences
- **Temperature 0.7**: Moderate variation - different phrasing and structure
- **Temperature 1.0**: High variation - creative, diverse responses

### Recommended Setting
**temperature = 0.2**

**Rationale:**
- Lower temperature (0.0-0.3) gives more predictable, consistent responses
- Useful when answers should stay close to retrieved evidence
- Reduces unnecessary variation in factual responses
- For a grounded public-health assistant, consistency is more valuable than creativity
- Temperature 0.2 provides slight flexibility while maintaining strong consistency

**Important:** Low temperature does NOT eliminate hallucinations. Factuality primarily depends on:
- Retrieval quality
- Grounding in source documents
- Source quality and currency
- Prompt design and validation

## max_tokens

### What it does
max_tokens controls the maximum number of tokens the model can generate in its response, effectively capping response length.

### Experiment Results
**Note:** Actual experiment results require API credentials to run.

Expected observations:
- **max_tokens = 20**: Very short answers, likely truncated mid-sentence
- **max_tokens = 50**: Moderate length, may truncate complex explanations
- **max_tokens = 150+**: Complete answers with full explanations

### Recommended Setting
**max_tokens = 300**

**Rationale:**
- Prevents unnecessarily long answers that could drift from the question
- Helps keep output predictable and focused
- Limits potential generation cost
- Large enough to provide complete grounded answers for most public health queries
- Small enough to prevent verbose, meandering responses
- Tradeoff: too small can truncate important information, too large can increase cost and reduce focus

## top_p

### What it does
top_p (nucleus sampling) controls token selection by restricting to the smallest set of tokens whose cumulative probability exceeds the threshold. Lower values make generation more constrained.

### Experiment Results
**Note:** Actual experiment results require API credentials to run.

Expected observations:
- **top_p = 0.1**: Highly constrained, only considers most likely tokens
- **top_p = 0.5**: Moderate constraint, balances focus and diversity
- **top_p = 1.0**: No constraint, considers all tokens (default behavior)

### Recommended Setting
**top_p = 1.0**

**Rationale:**
- Keep top_p at its default value
- Use temperature as the primary tuning parameter
- Avoid aggressively tuning both temperature and top_p simultaneously
- Simple configuration is easier to understand and maintain
- For grounded RAG, temperature alone provides sufficient control over response variability

## Recommended Configuration

For a factual, grounded RAG assistant serving public health guidance:

```python
temperature: 0.2
max_tokens: 300
top_p: 1.0
```

**Reasoning:**
1. **Temperature 0.2** provides consistent, predictable responses while allowing minor flexibility for natural language variation
2. **max_tokens 300** ensures complete answers without excessive verbosity, balancing completeness with cost control
3. **top_p 1.0** uses the default nucleus sampling behavior, keeping the configuration simple and avoiding unnecessary complexity

This configuration prioritizes:
- Consistency in factual responses
- Complete but concise answers
- Simple, maintainable parameter settings
- Cost-effective generation

## Configuration File

Add these settings to your application configuration:

```python
# RAG Assistant Generation Parameters
RAG_TEMPERATURE = 0.2
RAG_MAX_TOKENS = 300
RAG_TOP_P = 1.0
```

## Next Steps

1. Configure your `.env` file with valid API credentials
2. Run the experiment script to generate actual results
3. Review the generated outputs in `experiments/outputs/`
4. Adjust parameters based on your specific use case and observations
5. Integrate the recommended settings into your RAG application

## Cost Considerations

The experiments are designed to be cost-effective:
- Temperature: 4 values × 1 run = 4 API calls
- max_tokens: 3 values × 1 run = 3 API calls  
- top_p: 3 values × 1 run = 3 API calls
- **Total: 10 API calls**

For more statistical significance, increase `runs_per_temp` in the script to 2-3 runs per temperature (total: 13-16 API calls).

## Notes

- These recommendations are specific to factual, grounded RAG assistants
- Different use cases (creative writing, brainstorming, etc.) may require different settings
- Always validate parameter choices against your specific application requirements
- Monitor actual usage and costs in production
