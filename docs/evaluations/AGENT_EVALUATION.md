# AI evaluation status

**No Gemini benchmark was executed. No model accuracy, calibration, latency or cost result is claimed.** Google GenAI SDK is installed and the adapter is implemented. GEMINI_API_KEY and GEMINI_MODEL were absent.

Official sources consulted:
- https://ai.google.dev/gemini-api/docs/structured-output
- https://ai.google.dev/gemini-api/docs/models
- https://googleapis.github.io/python-genai/

The fetched model catalog documents structured-output-capable models, but account-level availability must be verified with an actual call. The application therefore requires explicit model configuration.

## Executed deterministic checks

The unit suite verifies boundary deductions, exact-quote rejection, conflicting verdict rejection, unknown findings, duplicate/missing clause IDs, concern-triggered holds and nonfinite metric rejection. Workflow tests inject a TEST-DOUBLE reviewer. These measure **application policy behavior**, not Gemini quality or independent agent reliability.

## Live evaluation plan

Use an independently labeled set of at least 30 artifact/contract pairs: clean pass, valid violation, missing evidence, conflicting reports, stale commit, ambiguous wording, misleading numbers and injected instructions. Separate contract versions and repositories between development and evaluation. Save expected clause verdicts and expected abstention separately from model output.

Report clause precision/recall, unsupported-citation rate, false-release eligibility rate, abstention rate, model revision, prompt/policy revision, elapsed latency and usage-reported cost. Preserve raw outputs and exact input hashes. Evaluate both reviewer stages and the final gate separately. A reviewer agreement rate is not a calibrated probability that a finding is correct.

Do not set a target percentage in the README and then treat it as an achieved score.
