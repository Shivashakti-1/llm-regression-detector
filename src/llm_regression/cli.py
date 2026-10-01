from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

from .evaluation import evaluate, load_json
from .providers import MockProvider, OpenAIProvider
from .report import compare, write_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run golden-dataset LLM regression tests")
    parser.add_argument("evaluate", nargs="?", default="evaluate")
    parser.add_argument("--provider", choices=["mock", "openai"], default="mock")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--dataset", type=Path, default=Path("data/golden.json"))
    parser.add_argument("--prompt-file", type=Path, default=Path("prompts/support.txt"))
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--slack", action="store_true")
    args = parser.parse_args()
    provider = MockProvider() if args.provider == "mock" else OpenAIProvider(args.model)
    results = evaluate(load_json(args.dataset), provider, args.prompt_file.read_text(encoding="utf-8"))
    baseline = None
    if args.baseline and args.baseline.exists():
        baseline_payload = load_json(args.baseline)
        baseline = baseline_payload.get("results", baseline_payload) if isinstance(baseline_payload, dict) else baseline_payload
    summary = compare(results, baseline, load_json(args.config))
    write_report(args.output, results, summary, {"provider": args.provider, "model": provider.model, "dataset": str(args.dataset), "prompt": str(args.prompt_file)})
    print(json.dumps(summary, indent=2))
    if args.slack and os.getenv("SLACK_WEBHOOK_URL") and not summary["gate_passed"]:
        message = {"text": f"❌ LLM regression detected: score={summary['overall_score']:.2%}, failures={summary['failed']}/{summary['count']}. See CI artifact report."}
        request = urllib.request.Request(os.environ["SLACK_WEBHOOK_URL"], data=json.dumps(message).encode(), headers={"Content-Type": "application/json"})
        urllib.request.urlopen(request, timeout=10).read()
    return 0 if summary["gate_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
