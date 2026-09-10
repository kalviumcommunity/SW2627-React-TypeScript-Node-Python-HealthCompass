"""Repeatable parameter experiments; never turn expected behavior into measured results."""

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from statistics import mean
import sys

from dotenv import load_dotenv
from openai import APIError, OpenAI

BASE_PROMPT = """Answer using only this context:
HealthCompass stores official guidance with versions, effective dates, regions,
and approval status. Current approved guidance is applicable only to its stated
region and effective period. Superseded guidance is retained for historical use.
Question: Why should the assistant check approval, region and effective date?
Give a short explanation. End with the literal marker END_OF_ANSWER."""


def experiment_cases(repetitions: int = 3, token_limit_parameter: str = "max_completion_tokens") -> list[dict]:
    """Hold prompt and other controls fixed within each comparison."""
    if type(repetitions) is not int or repetitions < 2:
        raise ValueError("Use at least two repetitions to compare variation")
    if token_limit_parameter not in {"max_completion_tokens", "max_tokens"}:
        raise ValueError("Unsupported token limit parameter")
    groups = {
        "temperature": [0.0, 0.3, 0.7, 1.0],
        "output_limit": [20, 50, 150],
        "top_p": [0.1, 0.5, 1.0],
        "stop": [None, ["END_OF_ANSWER"]],
    }
    cases = []
    for parameter, values in groups.items():
        for value in values:
            # Top-p experiments leave temperature at the API default.
            settings = {token_limit_parameter: 300}
            if parameter != "top_p":
                settings["temperature"] = 0.3
            key = token_limit_parameter if parameter == "output_limit" else parameter
            if value is not None:
                settings[key] = value
            for run in range(1, repetitions + 1):
                cases.append({"parameter": parameter, "value": value,
                              "run": run, "settings": settings.copy()})
    return cases


class ExperimentRunner:
    def __init__(self, client, model: str):
        if not model or not model.strip():
            raise ValueError("CHAT_MODEL must be configured")
        self.client = client
        self.model = model

    def run(self, cases: list[dict]) -> list[dict]:
        records = []
        for case in cases:
            record = {**case, "requested_model": self.model,
                      "timestamp": datetime.now(timezone.utc).isoformat()}
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": "Use only the supplied context."},
                              {"role": "user", "content": BASE_PROMPT}],
                    **case["settings"],
                )
                if not response.choices:
                    raise ValueError("No response choices")
                choice = response.choices[0]
                content = choice.message.content
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("No text response")
                record.update(status="success", content=content,
                              finish_reason=choice.finish_reason,
                              response_model=response.model,
                              system_fingerprint=getattr(response, "system_fingerprint", None),
                              usage=response.usage.model_dump() if response.usage else None)
            except (APIError, ValueError) as exc:
                # Provider messages may echo credentials or request details. Record type/status only.
                record.update(status="error", error_type=type(exc).__name__,
                              http_status=getattr(exc, "status_code", None))
            records.append(record)
        return records


def summarize(records: list[dict]) -> dict:
    groups = defaultdict(list)
    for record in records:
        groups[(record["parameter"], json.dumps(record["value"]))].append(record)
    comparisons = []
    for (parameter, value), group in groups.items():
        successful = [record for record in group if record["status"] == "success"]
        completion_tokens = [r["usage"]["completion_tokens"] for r in successful
                             if r["usage"] and r["usage"].get("completion_tokens") is not None]
        comparisons.append({
            "parameter": parameter, "value": json.loads(value),
            "attempted": len(group), "successful": len(successful),
            "failed": len(group) - len(successful),
            "distinct_outputs": len({r["content"] for r in successful}) if successful else None,
            "length_limited": sum(r["finish_reason"] == "length" for r in successful),
            "mean_completion_tokens": mean(completion_tokens) if completion_tokens else None,
            "usage_samples": len(completion_tokens),
            "outputs_containing_marker": sum("END_OF_ANSWER" in r["content"] for r in successful),
        })
    return {"attempted": len(records),
            "successful": sum(r["status"] == "success" for r in records),
            "failed": sum(r["status"] == "error" for r in records),
            "comparisons": comparisons}


def write_report(path: Path, records: list[dict]) -> None:
    """Write raw measurements and derived metrics, refusing to overwrite prior evidence."""
    report = {
        "schema_version": 1, "prompt": BASE_PROMPT,
        "limitations": [
            "Output variation is observed, not guaranteed by temperature.",
            "finish_reason=stop may mean natural completion or a stop sequence.",
            "These comparisons do not measure factual correctness or grounding.",
            "API usage is recorded when supplied; no currency cost is inferred.",
        ],
        "summary": summarize(records), "records": records,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--token-limit-parameter", choices=["max_completion_tokens", "max_tokens"],
                        default="max_completion_tokens")
    parser.add_argument("--output", type=Path, default=Path("outputs/parameter-experiments.json"))
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without API calls")
    args = parser.parse_args(argv)
    try:
        cases = experiment_cases(args.repetitions, args.token_limit_parameter)
        if args.dry_run:
            print(json.dumps({"planned_calls": len(cases), "prompt": BASE_PROMPT, "cases": cases}, indent=2))
            return 0
        if args.output.exists():
            raise ValueError("Output already exists; choose a new --output path")
        load_dotenv()
        required = ["OPENAI_API_KEY", "CHAT_MODEL"]
        if any(not os.getenv(key, "").strip() for key in required):
            raise ValueError("Configure OPENAI_API_KEY and CHAT_MODEL before a live run")
        # No automatic retries: attempted records correspond to explicit SDK calls.
        with OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                    base_url=os.getenv("OPENAI_BASE_URL") or None,
                    timeout=30, max_retries=0) as client:
            records = ExperimentRunner(client, os.environ["CHAT_MODEL"]).run(cases)
        write_report(args.output, records)
        summary = summarize(records)
        print(f"Attempted {summary['attempted']}; successful {summary['successful']}; "
              f"failed {summary['failed']}. Report: {args.output}")
        return 1 if summary["failed"] else 0
    except (ValueError, OSError) as exc:
        print(f"Experiment error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
