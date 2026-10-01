from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .providers import Provider


@dataclass
class CaseResult:
    id: str
    input: str
    expected: str
    actual: str
    score: float
    passed: bool
    tags: list[str]
    missing_keywords: list[str]


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def score_case(case: dict[str, Any], actual: str) -> tuple[float, list[str]]:
    required = [str(k).lower() for k in case.get("required_keywords", [])]
    actual_tokens = _tokens(actual)
    missing = [keyword for keyword in required if keyword not in actual_tokens and keyword not in actual.lower()]
    keyword_score = 1.0 if not required else (len(required) - len(missing)) / len(required)
    expected_tokens = _tokens(case.get("expected", ""))
    overlap = len(expected_tokens & actual_tokens) / max(1, len(expected_tokens))
    return round((0.7 * keyword_score) + (0.3 * overlap), 4), missing


def evaluate(dataset: list[dict[str, Any]], provider: Provider, prompt: str, pass_score: float = 0.8) -> list[CaseResult]:
    results = []
    for case in dataset:
        actual = provider.generate(prompt, case["input"])
        score, missing = score_case(case, actual)
        results.append(CaseResult(case["id"], case["input"], case["expected"], actual, score, score >= pass_score, case.get("tags", []), missing))
    return results


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize(results: list[CaseResult]) -> dict[str, Any]:
    scores = [r.score for r in results]
    return {"count": len(results), "passed": sum(r.passed for r in results), "failed": sum(not r.passed for r in results), "overall_score": round(sum(scores) / max(1, len(scores)), 4), "failure_rate": round(sum(not r.passed for r in results) / max(1, len(results)), 4)}


def serialize(results: list[CaseResult]) -> list[dict[str, Any]]:
    return [asdict(result) for result in results]
