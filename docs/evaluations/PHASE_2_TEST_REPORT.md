# Phase 2 — Executed checks

Date: 2026-11-08 IST.

| Check | Actual result | Receipt |
|---|---|---|
| Backend unit/integration suite | **89 passed in 4.41 seconds** | `pytest-phase2.txt`, `junit-phase2.xml` |
| Statement coverage | **699 / 755 statements = 92.58%** | `coverage-phase2.json`, `coverage-phase2.txt` |
| Real report parsing | Generated Coverage.py report parsed; recomputed coverage equals report counts | `real-report-parser-check.json` |
| Frontend production build | Passed with Next.js 15.5.29, including TypeScript checks | `web-build-phase2.txt` |
| Real local HTTP smoke | Passed: health, four report imports, fixture verification, $4,500 proposal, hypothetical $5,000, authorization rejection | `http-smoke-phase2.json` |
| Offline passport replay | Passed through exported JSON and CLI; no external call | Same HTTP smoke receipt |
| Real provider calls | Not executed | Gemini / PayPal credentials unavailable |
| PostgreSQL / Docker | Not executed | No installed PostgreSQL server or Docker runtime found |
| Authenticated browser E2E | Not executed | Build and API tests do not establish full browser behavior |

Coverage was measured with Coverage.py 7.17.2 over `apps/api/covenantx`. It is statement coverage, not branch coverage, model accuracy, security assurance or external integration success. The AI adapter has uncovered real-model paths because no Gemini key/model was available. Payment workflows and recovery use explicit provider doubles in the suite.

## Additional failure cases exercised

- Duplicate JSON keys and nonfinite numbers.
- Conflicting coverage totals, contradictory explicit statement percentages and zero statements.
- k6 empty request counts, invalid time-trend types, missing P95 and out-of-range percentiles.
- SARIF incomplete/failed/contradictory invocations, unknown rules, invalid rule indices, unsupported versions, external properties and ambiguous suppressed/resolved findings.
- Duplicate artifact metrics, duplicate filenames and path-like filenames.
- Imported-file failures leave previous approval untouched.
- Draft editing rejected after contract approval.
- Historical replay checks original artifact bytes, derivation receipts, input hashes and recomputed deductions.
- Tampered records fail replay even if their outer digest could be recomputed.
- Candidate-order recovery is client-only, revision-bound, grace-period-bound and amount/snapshot-bound.
- Capture uncertainty remains blocked through unfamiliar provider states and legacy records lacking the newer marker.
- Chunked request bodies are capped without relying on Content-Length.
- Clause IDs cannot collide with graph root IDs.

## Reproduce

```bash
python -m pip install -r requirements-dev.txt
python -m coverage run --source=apps/api/covenantx -m pytest -q
python -m coverage json -o coverage.json
python -m coverage report
python scripts/http_smoke.py
```

From `apps/web`:

```bash
npm ci
npm run build
```

## Environmental interruption

When this conversation resumed, the workspace source was intact but installed Python dependencies were missing. An initial coverage command therefore failed with `No module named pytest`. Restoring the pinned requirements resolved that environment issue. The results above are from the successful subsequent execution, not the failed attempt.
