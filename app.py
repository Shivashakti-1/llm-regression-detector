from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from llm_regression.evaluation import evaluate, load_json, serialize, summarize
from llm_regression.providers import MockProvider, OpenAIProvider

st.set_page_config(page_title="LLM Regression Detector", page_icon="🧪", layout="wide")
st.title("🧪 LLM Regression Detector")
st.caption("Test prompt and model changes against a golden dataset before they reach users.")

with st.sidebar:
    st.header("Evaluation settings")
    provider_name = st.selectbox("Provider", ["mock", "openai"])
    model = st.text_input("Model", "gpt-4o-mini", disabled=provider_name == "mock")
    pass_score = st.slider("Case pass score", 0.0, 1.0, 0.8, 0.05)

default_dataset = Path(__file__).parent / "data" / "golden.json"
default_prompt = Path(__file__).parent / "prompts" / "support.txt"

left, right = st.columns(2)
with left:
    st.subheader("Prompt")
    prompt = st.text_area("System prompt", default_prompt.read_text(encoding="utf-8"), height=180, label_visibility="collapsed")
with right:
    st.subheader("Golden dataset")
    upload = st.file_uploader("Upload a JSON dataset", type=["json"])
    if upload:
        try:
            dataset = json.loads(upload.getvalue().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            st.error(f"Invalid JSON file: {exc}")
            dataset = []
    else:
        dataset = load_json(default_dataset)
    st.caption(f"{len(dataset)} test case(s) loaded")

if st.button("Run evaluation", type="primary", use_container_width=True):
    try:
        if provider_name == "mock":
            provider = MockProvider()
        else:
            if "OPENAI_API_KEY" in st.secrets:
                os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
            provider = OpenAIProvider(model)
        results = evaluate(dataset, provider, prompt, pass_score=pass_score)
        summary = summarize(results)
        summary["gate_passed"] = summary["overall_score"] >= pass_score and summary["failed"] == 0
        payload = {"summary": summary, "results": serialize(results), "model": provider.model}
        st.session_state["evaluation"] = payload
    except Exception as exc:
        st.error(str(exc))

if "evaluation" in st.session_state:
    payload = st.session_state["evaluation"]
    summary = payload["summary"]
    st.divider()
    st.subheader("Results")
    if summary["gate_passed"]:
        st.success("PASS — no quality regression detected")
    else:
        st.error("FAIL — quality regression detected")
    metric_columns = st.columns(4)
    metric_columns[0].metric("Overall score", f"{summary['overall_score']:.1%}")
    metric_columns[1].metric("Passed", f"{summary['passed']}/{summary['count']}")
    metric_columns[2].metric("Failed", summary["failed"])
    metric_columns[3].metric("Failure rate", f"{summary['failure_rate']:.1%}")
    st.dataframe(payload["results"], use_container_width=True, hide_index=True)
    report_bytes = json.dumps(payload, indent=2).encode("utf-8")
    st.download_button("Download JSON report", report_bytes, "results.json", "application/json")
