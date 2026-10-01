from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .evaluation import CaseResult, serialize, summarize


def compare(candidate: list[CaseResult], baseline: list[dict[str, Any]] | None, config: dict[str, Any]) -> dict[str, Any]:
    summary = summarize(candidate)
    baseline_by_id = {row["id"]: row for row in (baseline or [])}
    regressions = []
    for result in candidate:
        old = baseline_by_id.get(result.id)
        if old and result.score < old["score"] - config.get("maximum_slice_drop", 0.15):
            regressions.append({"id": result.id, "baseline": old["score"], "candidate": result.score})
    summary["regressions"] = regressions
    summary["gate_passed"] = (summary["overall_score"] >= config.get("minimum_score", 0.8) and summary["failure_rate"] <= config.get("maximum_failure_rate", 0.1) and not regressions)
    return summary


def write_report(output_dir: Path, results: list[CaseResult], summary: dict[str, Any], metadata: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {"metadata": metadata, "summary": summary, "results": serialize(results)}
    (output_dir / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    rows = "".join(f"<tr class='{('pass' if r.passed else 'fail')}'><td>{html.escape(r.id)}</td><td>{r.score:.2f}</td><td>{html.escape(r.actual)}</td><td>{html.escape(', '.join(r.missing_keywords) or '—')}</td></tr>" for r in results)
    regressions = html.escape(json.dumps(summary.get("regressions", [])))
    document = f"""<!doctype html><html><head><meta charset='utf-8'><title>LLM Evaluation Report</title><style>body{{font:16px system-ui;margin:2rem;max-width:1100px}}.cards{{display:flex;gap:1rem}}.card{{padding:1rem;background:#f1f5f9;border-radius:8px}}table{{width:100%;border-collapse:collapse;margin-top:1rem}}td,th{{padding:.6rem;border-bottom:1px solid #ddd;text-align:left}}.pass{{background:#ecfdf5}}.fail{{background:#fef2f2}}.status{{font-size:1.3rem;font-weight:700}}</style></head><body><h1>LLM Regression Report</h1><p class='status'>{'✅ PASS' if summary['gate_passed'] else '❌ FAIL'}</p><div class='cards'><div class='card'>Overall<br><b>{summary['overall_score']:.2%}</b></div><div class='card'>Passed<br><b>{summary['passed']}/{summary['count']}</b></div><div class='card'>Failure rate<br><b>{summary['failure_rate']:.2%}</b></div></div><p>Model: {html.escape(str(metadata.get('model')))} · Provider: {html.escape(str(metadata.get('provider')))}</p><h2>Cases</h2><table><tr><th>Case</th><th>Score</th><th>Output</th><th>Missing keywords</th></tr>{rows}</table><h2>Regressions</h2><pre>{regressions}</pre></body></html>"""
    (output_dir / "report.html").write_text(document, encoding="utf-8")
