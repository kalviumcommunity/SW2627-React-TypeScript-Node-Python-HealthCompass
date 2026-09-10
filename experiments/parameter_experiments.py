"""
LLM Parameter Experiments for Grounded RAG

This script experiments with different LLM generation parameters to understand
their effects on responses for a factual, grounded RAG assistant.
"""

import os
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv
from openai import OpenAI


# Consistent prompt for all experiments
BASE_PROMPT = """Answer the following question using ONLY the provided context.

Context:
The HealthCompass public-health guidance repository contains official documents with version numbers, effective dates, geographic applicability, and approval status. Active and approved guidance should be preferred over superseded or expired guidance.

Question:
Why should a RAG assistant prioritize current and approved guidance instead of relying on an older document version?

Give a concise factual explanation."""

# Longer prompt for max_tokens experiment
LONGER_PROMPT = """Explain why a RAG assistant should prioritize current approved guidance over superseded guidance. Explain the importance of version, effective date, source authority, geographic applicability, and citations."""


class ExperimentRunner:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("CHAT_MODEL")
        self.api_calls = 0
        
    def make_api_call(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Make an API call and track usage."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            self.api_calls += 1
            return {
                "content": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "total_tokens": response.usage.total_tokens if response.usage else None,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
            }
        except Exception as e:
            print(f"API Error: {e}")
            return {
                "content": f"ERROR: {str(e)}",
                "finish_reason": "error",
                "total_tokens": None,
                "prompt_tokens": None,
                "completion_tokens": None,
            }

    def run_temperature_experiment(self, temperatures: List[float], runs_per_temp: int = 1) -> List[Dict[str, Any]]:
        """Run temperature experiments with consistent prompt."""
        print(f"\n=== Temperature Experiment ===")
        results = []
        
        for temp in temperatures:
            print(f"\nTesting temperature {temp}...")
            for run in range(1, runs_per_temp + 1):
                print(f"  Run {run}/{runs_per_temp}")
                response = self.make_api_call(
                    messages=[{"role": "user", "content": BASE_PROMPT}],
                    temperature=temp,
                    max_tokens=300
                )
                results.append({
                    "parameter": "temperature",
                    "value": temp,
                    "run": run,
                    "timestamp": datetime.now().isoformat(),
                    "model": self.model,
                    **response
                })
        
        return results

    def run_max_tokens_experiment(self, max_tokens_values: List[int]) -> List[Dict[str, Any]]:
        """Run max_tokens experiments with longer prompt."""
        print(f"\n=== Max Tokens Experiment ===")
        results = []
        
        for max_tok in max_tokens_values:
            print(f"\nTesting max_tokens {max_tok}...")
            response = self.make_api_call(
                messages=[{"role": "user", "content": LONGER_PROMPT}],
                temperature=0.3,
                max_tokens=max_tok
            )
            results.append({
                "parameter": "max_tokens",
                "value": max_tok,
                "run": 1,
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                **response
            })
        
        return results

    def run_top_p_experiment(self, top_p_values: List[float]) -> List[Dict[str, Any]]:
        """Run top_p experiments with consistent prompt and fixed temperature."""
        print(f"\n=== Top P Experiment ===")
        results = []
        
        for top_p in top_p_values:
            print(f"\nTesting top_p {top_p}...")
            response = self.make_api_call(
                messages=[{"role": "user", "content": BASE_PROMPT}],
                temperature=0.3,
                top_p=top_p,
                max_tokens=300
            )
            results.append({
                "parameter": "top_p",
                "value": top_p,
                "run": 1,
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                **response
            })
        
        return results

    def save_temperature_results(self, results: List[Dict[str, Any]], output_path: str):
        """Save temperature experiment results to markdown file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Temperature Experiment\n\n")
            f.write("## Prompt\n\n")
            f.write("```\n")
            f.write(BASE_PROMPT)
            f.write("\n```\n\n")
            
            # Group by temperature
            from collections import defaultdict
            by_temp = defaultdict(list)
            for r in results:
                by_temp[r['value']].append(r)
            
            for temp in sorted(by_temp.keys()):
                f.write(f"## Temperature {temp}\n\n")
                for i, r in enumerate(by_temp[temp], 1):
                    f.write(f"### Run {i}\n\n")
                    f.write(f"**Output:**\n\n")
                    f.write(r['content'])
                    f.write("\n\n")
                    f.write(f"**Tokens:** {r['completion_tokens']} (completion), {r['total_tokens']} (total)\n\n")
                    f.write(f"**Observation:** ")
                    if temp == 0.0:
                        f.write("Deterministic output - should be identical across runs.\n")
                    elif temp < 0.5:
                        f.write("Low variation expected - consistent wording.\n")
                    else:
                        f.write("Higher variation expected - more creative wording.\n")
                    f.write("\n")
            
            f.write("## Conclusion\n\n")
            f.write("LOW TEMPERATURE (0.0-0.3):\n")
            f.write("- More stable, predictable, and consistent wording\n")
            f.write("- Suitable for factual, grounded responses\n")
            f.write("- Reduces unnecessary variation in answers\n\n")
            f.write("HIGHER TEMPERATURE (0.7-1.0):\n")
            f.write("- More variation in wording and structure\n")
            f.write("- Potentially more creative or diverse responses\n")
            f.write("- May introduce unnecessary variation for factual queries\n\n")
            f.write("IMPORTANT: Temperature does NOT guarantee factual correctness. ")
            f.write("Factuality primarily depends on retrieval quality, grounding, source quality, and prompt design.\n")
        
        print(f"Temperature results saved to {output_path}")

    def save_max_tokens_results(self, results: List[Dict[str, Any]], output_path: str):
        """Save max_tokens experiment results to markdown file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Max Tokens Experiment\n\n")
            f.write("## Prompt\n\n")
            f.write("```\n")
            f.write(LONGER_PROMPT)
            f.write("\n```\n\n")
            
            f.write("| Max Tokens | Completion Tokens | Total Tokens | Complete? | Output |\n")
            f.write("|------------|-------------------|--------------|-----------|--------|\n")
            
            for r in results:
                complete = "Yes" if r['finish_reason'] == 'stop' else f"No ({r['finish_reason']})"
                # Truncate output for table
                output_preview = r['content'][:100] + "..." if len(r['content']) > 100 else r['content']
                output_preview = output_preview.replace("\n", " ")
                f.write(f"| {r['value']} | {r['completion_tokens']} | {r['total_tokens']} | {complete} | {output_preview} |\n")
            
            f.write("\n## Detailed Outputs\n\n")
            for r in results:
                f.write(f"### Max Tokens: {r['value']}\n\n")
                f.write(f"**Output:**\n\n")
                f.write(r['content'])
                f.write("\n\n")
                f.write(f"**Completion Tokens:** {r['completion_tokens']}\n")
                f.write(f"**Total Tokens:** {r['total_tokens']}\n")
                f.write(f"**Finish Reason:** {r['finish_reason']}\n")
                f.write(f"**Complete:** {'Yes' if r['finish_reason'] == 'stop' else 'No'}\n\n")
            
            f.write("## Conclusion\n\n")
            f.write("Small max_tokens (e.g., 20):\n")
            f.write("- Very short answers, likely truncated\n")
            f.write("- May cut off important information\n\n")
            f.write("Medium max_tokens (e.g., 50):\n")
            f.write("- Moderate length answers\n")
            f.write("- May still truncate for complex responses\n\n")
            f.write("Larger max_tokens (e.g., 150+):\n")
            f.write("- More complete answers\n")
            f.write("- Allows for full explanation\n\n")
            f.write("max_tokens controls the maximum amount of generated output, ")
            f.write("helping control response length and generation cost.\n")
        
        print(f"Max tokens results saved to {output_path}")

    def save_top_p_results(self, results: List[Dict[str, Any]], output_path: str):
        """Save top_p experiment results to markdown file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Top P Experiment\n\n")
            f.write("## Prompt\n\n")
            f.write("```\n")
            f.write(BASE_PROMPT)
            f.write("\n```\n\n")
            f.write("**Fixed temperature:** 0.3\n\n")
            
            f.write("| Top P | Completion Tokens | Total Tokens | Output |\n")
            f.write("|-------|-------------------|--------------|--------|\n")
            
            for r in results:
                output_preview = r['content'][:100] + "..." if len(r['content']) > 100 else r['content']
                output_preview = output_preview.replace("\n", " ")
                f.write(f"| {r['value']} | {r['completion_tokens']} | {r['total_tokens']} | {output_preview} |\n")
            
            f.write("\n## Detailed Outputs\n\n")
            for r in results:
                f.write(f"### Top P: {r['value']}\n\n")
                f.write(f"**Output:**\n\n")
                f.write(r['content'])
                f.write("\n\n")
                f.write(f"**Completion Tokens:** {r['completion_tokens']}\n")
                f.write(f"**Total Tokens:** {r['total_tokens']}\n\n")
            
            f.write("## Conclusion\n\n")
            f.write("top_p controls nucleus sampling by restricting token selection to a probability mass.\n\n")
            f.write("Lower top_p (e.g., 0.1):\n")
            f.write("- More constrained generation\n")
            f.write("- Only considers most likely tokens\n")
            f.write("- More focused, predictable output\n\n")
            f.write("Medium top_p (e.g., 0.5):\n")
            f.write("- Moderate constraint\n")
            f.write("- Balances focus and diversity\n\n")
            f.write("top_p = 1.0:\n")
            f.write("- No nucleus sampling constraint\n")
            f.write("- Considers all tokens in probability distribution\n")
            f.write("- Standard default behavior\n\n")
            f.write("For grounded RAG, keeping top_p at default (1.0) and using temperature ")
            f.write("as the primary tuning parameter is generally recommended.\n")
        
        print(f"Top P results saved to {output_path}")

    def save_all_results(self, all_results: Dict[str, List[Dict[str, Any]]], output_path: str):
        """Save all experiment results to a combined markdown file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# All Parameter Experiment Results\n\n")
            f.write(f"**Model:** {self.model}\n")
            f.write(f"**Total API Calls:** {self.api_calls}\n")
            f.write(f"**Experiment Date:** {datetime.now().isoformat()}\n\n")
            
            for exp_name, results in all_results.items():
                f.write(f"## {exp_name.replace('_', ' ').title()}\n\n")
                f.write(f"**Tests run:** {len(results)}\n\n")
                
                for r in results:
                    f.write(f"### {r['parameter']} = {r['value']} (Run {r.get('run', 1)})\n\n")
                    f.write(f"**Output:**\n\n```\n")
                    f.write(r['content'])
                    f.write("\n```\n\n")
                    f.write(f"**Tokens:** {r['completion_tokens']} completion, {r['total_tokens']} total\n")
                    f.write(f"**Finish Reason:** {r['finish_reason']}\n\n")
        
        print(f"All results saved to {output_path}")


def main():
    print("Starting LLM Parameter Experiments...")
    
    runner = ExperimentRunner()
    
    # Configuration
    temperatures = [0.0, 0.3, 0.7, 1.0]
    max_tokens_values = [20, 50, 150]
    top_p_values = [0.1, 0.5, 1.0]
    runs_per_temp = 1  # Increase to 2-3 for more statistical significance
    
    # Create outputs directory if it doesn't exist
    os.makedirs("experiments/outputs", exist_ok=True)
    
    # Run experiments
    all_results = {}
    
    # Temperature experiment
    temp_results = runner.run_temperature_experiment(temperatures, runs_per_temp)
    all_results['temperature'] = temp_results
    runner.save_temperature_results(
        temp_results, 
        "experiments/outputs/temperature_comparison.md"
    )
    
    # Max tokens experiment
    max_tok_results = runner.run_max_tokens_experiment(max_tokens_values)
    all_results['max_tokens'] = max_tok_results
    runner.save_max_tokens_results(
        max_tok_results,
        "experiments/outputs/max_tokens_comparison.md"
    )
    
    # Top P experiment
    top_p_results = runner.run_top_p_experiment(top_p_values)
    all_results['top_p'] = top_p_results
    runner.save_top_p_results(
        top_p_results,
        "experiments/outputs/additional_parameter_comparison.md"
    )
    
    # Save all results
    runner.save_all_results(
        all_results,
        "experiments/outputs/all_results.md"
    )
    
    print(f"\n=== Experiment Complete ===")
    print(f"Total API calls made: {runner.api_calls}")
    print(f"Results saved to experiments/outputs/")


if __name__ == "__main__":
    main()
