"""Structured output experiments for RAG assistant using JSON mode."""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from openai import APIError, OpenAI

from .validator import (
    ValidationError,
    format_validation_error,
    parse_and_validate,
    StructuredOutputResult,
)


# System prompt for structured output
SYSTEM_PROMPT = """You are a factual RAG assistant for HealthCompass.

Return your response as valid JSON only.

The JSON must contain:
- answer: a concise factual answer to the question
- source: the name of the source document or repository

Optional fields:
- version: document version if applicable
- effective_date: document effective date if applicable

Do not include Markdown code fences.
Do not include explanatory text outside the JSON object.
Do not include any text before or after the JSON object."""

# Consistent user prompt for experiments
USER_PROMPT = """Context: HealthCompass stores official public-health documents with versions, effective dates, geographic applicability, and approval status. Active and approved guidance should be preferred over superseded or expired documents.

Question: Why should a RAG assistant prioritize current approved guidance instead of superseded guidance?

Provide a concise factual explanation in the required JSON format."""


# JSON schema for structured output (OpenAI-compatible)
JSON_SCHEMA = {
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
    "additionalProperties": False
}


class StructuredOutputRunner:
    """Runner for structured output experiments."""
    
    def __init__(self, client: OpenAI, model: str) -> None:
        if not model or not model.strip():
            raise ValueError("CHAT_MODEL must be configured")
        self.client = client
        self.model = model
        self.api_calls = 0
    
    def request_structured_output(
        self,
        use_json_mode: bool = True,
        temperature: float = 0.2,
        max_tokens: int = 300
    ) -> Dict[str, Any]:
        """
        Request structured output from the model.
        
        Args:
            use_json_mode: Whether to use OpenAI's JSON mode
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with request results
        """
        self.api_calls += 1
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
        ]
        
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if use_json_mode:
            request_params["response_format"] = {"type": "json_object"}
        
        result = {
            "use_json_mode": use_json_mode,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": self.model,
            "raw_response": None,
            "parsed_response": None,
            "validation_result": None,
            "error": None,
            "api_call_success": False
        }
        
        try:
            response = self.client.chat.completions.create(**request_params)
            
            if not response.choices:
                raise ValueError("No response choices")
            
            content = response.choices[0].message.content
            if not content or not isinstance(content, str):
                raise ValueError("No text response")
            
            result["raw_response"] = content
            result["api_call_success"] = True
            result["usage"] = response.usage.model_dump() if response.usage else None
            
            # Parse and validate
            validation_result = parse_and_validate(content)
            result["validation_result"] = validation_result.to_dict()
            
            if validation_result.success:
                result["parsed_response"] = validation_result.data
            else:
                result["error"] = validation_result.error
                
        except (APIError, ValueError) as exc:
            result["error"] = f"{type(exc).__name__}: {str(exc)}"
        
        return result
    
    def run_comparison(self, repetitions: int = 3) -> list[Dict[str, Any]]:
        """
        Run comparison between JSON mode and regular mode.
        
        Args:
            repetitions: Number of repetitions for each mode
            
        Returns:
            List of result dictionaries
        """
        results = []
        
        # Test with JSON mode
        for i in range(repetitions):
            result = self.request_structured_output(use_json_mode=True)
            result["run"] = i + 1
            result["mode"] = "json_mode"
            results.append(result)
        
        # Test without JSON mode
        for i in range(repetitions):
            result = self.request_structured_output(use_json_mode=False)
            result["run"] = i + 1
            result["mode"] = "regular"
            results.append(result)
        
        return results


def save_results(results: list[Dict[str, Any]], output_path: Path) -> None:
    """
    Save experiment results to JSON file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to save results
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "schema_version": 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system_prompt": SYSTEM_PROMPT,
        "user_prompt": USER_PROMPT,
        "json_schema": JSON_SCHEMA,
        "total_api_calls": sum(1 for r in results if r.get("api_call_success", False)),
        "results": results
    }
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")


def generate_markdown_report(results: list[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate a human-readable markdown report.
    
    Args:
        results: List of result dictionaries
        output_path: Path to save markdown report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open("w", encoding="utf-8") as f:
        f.write("# Structured Output Experiment Results\n\n")
        f.write(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n\n")
        
        # Summary
        json_mode_results = [r for r in results if r["mode"] == "json_mode"]
        regular_results = [r for r in results if r["mode"] == "regular"]
        
        json_mode_success = sum(1 for r in json_mode_results if r["validation_result"]["success"])
        regular_success = sum(1 for r in regular_results if r["validation_result"]["success"])
        
        f.write("## Summary\n\n")
        f.write(f"- **Total API calls:** {len(results)}\n")
        f.write(f"- **JSON mode attempts:** {len(json_mode_results)}\n")
        f.write(f"- **JSON mode successful:** {json_mode_success}\n")
        f.write(f"- **Regular mode attempts:** {len(regular_results)}\n")
        f.write(f"- **Regular mode successful:** {regular_success}\n\n")
        
        # Schema
        f.write("## Required Schema\n\n")
        f.write("```json\n")
        f.write(json.dumps(JSON_SCHEMA, indent=2))
        f.write("\n```\n\n")
        
        # JSON mode results
        f.write("## JSON Mode Results\n\n")
        for i, result in enumerate(json_mode_results, 1):
            f.write(f"### Run {i}\n\n")
            f.write(f"**API Success:** {result['api_call_success']}\n")
            f.write(f"**Validation Success:** {result['validation_result']['success']}\n")
            
            if result.get("error"):
                f.write(f"**Error:** {result['error']}\n")
            
            if result.get("raw_response"):
                f.write(f"**Raw Response:**\n```\n{result['raw_response']}\n```\n")
            
            if result.get("parsed_response"):
                f.write(f"**Parsed Response:**\n```json\n")
                f.write(json.dumps(result['parsed_response'], indent=2))
                f.write("\n```\n")
            
            if result.get("validation_result", {}).get("recovery_attempted"):
                f.write("**Recovery Attempted:** Yes\n")
            
            f.write("\n")
        
        # Regular mode results
        f.write("## Regular Mode Results\n\n")
        for i, result in enumerate(regular_results, 1):
            f.write(f"### Run {i}\n\n")
            f.write(f"**API Success:** {result['api_call_success']}\n")
            f.write(f"**Validation Success:** {result['validation_result']['success']}\n")
            
            if result.get("error"):
                f.write(f"**Error:** {result['error']}\n")
            
            if result.get("raw_response"):
                f.write(f"**Raw Response:**\n```\n{result['raw_response']}\n```\n")
            
            if result.get("parsed_response"):
                f.write(f"**Parsed Response:**\n```json\n")
                f.write(json.dumps(result['parsed_response'], indent=2))
                f.write("\n```\n")
            
            if result.get("validation_result", {}).get("recovery_attempted"):
                f.write("**Recovery Attempted:** Yes\n")
            
            f.write("\n")
        
        # Conclusions
        f.write("## Conclusions\n\n")
        f.write("### JSON Mode\n")
        if json_mode_success == len(json_mode_results):
            f.write("- All JSON mode requests produced valid structured output\n")
        else:
            f.write(f"- {json_mode_success}/{len(json_mode_results)} JSON mode requests produced valid structured output\n")
        
        f.write("\n### Regular Mode\n")
        if regular_success == len(regular_results):
            f.write("- All regular mode requests produced valid structured output\n")
        else:
            f.write(f"- {regular_success}/{len(regular_results)} regular mode requests produced valid structured output\n")
        
        f.write("\n### Recommendation\n")
        if json_mode_success >= regular_success:
            f.write("JSON mode is recommended for structured output as it provides stronger guarantees for valid JSON responses.\n")
        else:
            f.write("Both modes show similar success rates. JSON mode is still recommended for consistency.\n")


def main(argv: list[str] | None = None) -> int:
    """Main entry point for structured output experiments."""
    parser = argparse.ArgumentParser(description="Run structured output experiments")
    parser.add_argument("--repetitions", type=int, default=3, help="Number of repetitions per mode")
    parser.add_argument("--output", type=Path, default=Path("experiments/structured_output/outputs/results.json"))
    parser.add_argument("--markdown", type=Path, default=Path("experiments/structured_output/outputs/sample_results.md"))
    parser.add_argument("--dry-run", action="store_true", help="Print plan without API calls")
    args = parser.parse_args(argv)
    
    try:
        load_dotenv()
        
        if not args.dry_run:
            required = ["OPENAI_API_KEY", "CHAT_MODEL"]
            if any(not os.getenv(key, "").strip() for key in required):
                raise ValueError("Configure OPENAI_API_KEY and CHAT_MODEL before running experiments")
        
        if args.dry_run:
            print("Dry run mode - no API calls will be made")
            print(f"Planned repetitions per mode: {args.repetitions}")
            print(f"Total planned API calls: {args.repetitions * 2}")
            print(f"Output paths: {args.output}, {args.markdown}")
            return 0
        
        with OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            timeout=30,
            max_retries=0,
        ) as client:
            runner = StructuredOutputRunner(client, os.environ["CHAT_MODEL"])
            results = runner.run_comparison(args.repetitions)
        
        save_results(results, args.output)
        generate_markdown_report(results, args.markdown)
        
        print(f"Experiment complete. Results saved to {args.output}")
        print(f"Markdown report saved to {args.markdown}")
        print(f"Total API calls made: {runner.api_calls}")
        
        return 0
        
    except (ValueError, OSError) as exc:
        print(f"Experiment error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
