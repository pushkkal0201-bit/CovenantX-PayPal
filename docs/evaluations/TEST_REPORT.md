# Phase 1 verification history

For current source results, see [Phase 2 test report](PHASE_2_TEST_REPORT.md): 89 tests pass. The results below are retained as the initial-build history.

Build date: 2026-11-08 IST.

| Check | Command / operation | Observed result |
|---|---|---|
| Initial Python suite | `python -m pytest -q` | 41 passed in 2.87 s |
| Expanded final Python suite | `python -m pytest -q --junitxml=docs/evaluations/junit.xml` | 44 passed in 3.06 s |
| Production frontend build | `npm run build` in `apps/web` | Next.js 15.5.29 compiled, type checks passed, static routes generated |
| Migration | `python -m alembic upgrade head` | Exit 0 on local SQLite |
| Browser | `sites-preview` + cloud browser | Login layout rendered and visually inspected |
| Initial preview | Next.js received `--host` | FAILED; repaired with compatible dev launcher |
| Local standalone API probe | HTTPX against localhost | FAILED: first proxy dependency error, later process connection refused; no running-server success claimed |

The local API behavior is verified in FastAPI TestClient integration tests, not by a persistent browser-to-API session. Preview and standalone processes have separate runtime lifetimes in this environment. The authenticated UI workflow, mobile browser layout and full production deployment have not been verified.

The final build was rerun after the active-evidence inspection panel was added; it passed. The final test run followed the capture-to-GET reconciliation change. SDK schema configuration and async context-manager support were inspected successfully after installing the declared SOCKS dependency; this did not make a provider call.

## Successful real HTTP smoke

After the standalone process-lifetime failure, `python scripts/http_smoke.py` ran an owned Uvicorn subprocess and HTTPX client in one lifecycle. It returned HTTP 200 health, a SIMULATED $4,500 proposal, a $5,000 hypothetical result and HTTP 409 for attempted fixture authorization. No external provider was called. The raw receipt is `http-smoke.json`.

## Coverage areas

- Authorization and role restrictions; missing object handling.
- Contract amount validation; finite metric bounds; exact Decimal thresholds.
- Duplicate/stale revisions and concurrent settlement approval.
- Demonstration and fixture payment gates.
- Evidence replacement and dispute invalidation of prior approval.
- Payment-state mutation locks.
- Nonmutating settlement counterfactual.
- Graph edges and passport digest/tamper detection.
- Create timeout with stable key; expiry of retry window.
- Capture timeout without recapture; payer approval requirement.
- Provider amount mismatch; completed-state monotonicity.
- Webhook signature rejection and event replay handling using a fake provider.
- Persistence across application restart.
- Real AI unavailable path does not fall back to fixtures.
- HTTPX sandbox host, request payload, OAuth flow and idempotency header with MockTransport.
- Untrusted approval URL rejection.

Raw `pytest-output.txt` and JUnit XML accompany this report. Passing tests do not establish production security, PostgreSQL correctness, PayPal account eligibility, signed webhook delivery or Gemini accuracy.
