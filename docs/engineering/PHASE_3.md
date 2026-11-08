# Phase 3 — External integration preparation

The first increment adds a local configuration preflight before the real-provider acceptance workflow.

- Fixture checks validate role-token separation, browser origin syntax and supported database driver prefixes.
- Sandbox checks additionally require Gemini key/model and PayPal merchant configuration.
- Optional webhook checking requires the registered sandbox webhook ID.
- JSON and terminal output expose only check names, outcomes and fixed remedies. No configuration values are printed.
- Environment precedence matches the existing launcher; configuration files are never modified.

Run `python scripts/preflight.py --mode sandbox --webhook --json` before the manual acceptance steps in `docs/submission/SUBMISSION_READINESS.md`.

This increment makes no external calls. Credential validity, model availability, database connections and genuine PayPal approval/capture remain acceptance work requiring the configured accounts. It does not complete Phase 3.

Targeted regression coverage checks fixture versus sandbox requirements, redaction, invalid origins, identical role tokens, webhook requirements and environment precedence.

Validation: `python -m pytest --noconftest -q tests/test_preflight.py` — 4 passed. The local runtime lacks the API dependencies, so this focused run skips the application fixture configuration; the repository CI runs the full suite.
