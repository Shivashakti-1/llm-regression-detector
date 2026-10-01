# LLM Regression Detector

CI/CD-style evaluation for LLM-powered features. Every prompt or model change can be tested against a versioned golden dataset, compared with a baseline, and blocked when quality drops.

## Quick start

```powershell
cd C:\shiva\llm-regression-detector
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python -m llm_regression evaluate --provider mock --dataset data/golden.json --output artifacts
```

The command writes `artifacts/report.html`, `artifacts/results.json`, and exits with code `1` when the candidate is below the configured quality gate.

## OpenAI mode

```powershell
$env:OPENAI_API_KEY = "..."
python -m llm_regression evaluate `
  --provider openai `
  --model gpt-4o-mini `
  --prompt-file prompts/support.txt `
  --dataset data/golden.json `
  --output artifacts
```

The API client uses the current OpenAI Python SDK and only sends the test case input plus the configured prompt. Keep secrets in GitHub Actions secrets, never in the dataset or repository.

## Run the browser dashboard

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown by Streamlit. The dashboard supports mock evaluations without an API key and OpenAI evaluations with `OPENAI_API_KEY` configured.

## Regression policy

The default gate requires:

- overall score to be at least `0.80`;
- no more than `10%` of cases to fail;
- no tag/slice to fall by more than `0.15` versus the baseline, when a baseline exists.

Tune these values in `config.json` or with CLI flags. A baseline is the prior `results.json`; in CI, download it from an artifact or commit a reviewed baseline file.

## CI

The GitHub Actions workflow runs on pull requests that change prompts, evaluator code, or the golden dataset. It publishes the HTML report and optionally posts a Slack alert when `SLACK_WEBHOOK_URL` is configured.

## Project layout

```text
data/golden.json                 test cases and expected behavior
prompts/support.txt              versioned prompt under test
src/llm_regression/              evaluator, providers, reporting, CLI
tests/                            unit tests
.github/workflows/evaluate.yml   pull-request quality gate
```
