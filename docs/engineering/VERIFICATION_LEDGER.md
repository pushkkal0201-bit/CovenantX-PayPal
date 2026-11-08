# Verification ledger

Date: 2026-11-08 IST. Execution receipts are from this build session; elapsed times are observed local test durations, not benchmarks.

| ID | Files / operation | Evidence | Status | Limitation |
|---|---|---|---|---|
| CX-001 | Source discovery | Attachment inspection; Library title searches; GitHub repository search | VERIFIED | No starting source found; new implementation |
| CX-002 | `domain.py`, `store.py`, `main.py` | Phase 1 JUnit XML, 44 tests across initial suite | VERIFIED locally | SQLite / injected provider coverage |
| CX-003 | `paypal.py` | MockTransport + workflow test doubles | SIMULATED provider responses | No actual sandbox receipt |
| CX-004 | `ai.py` | SDK import; missing-credentials and fake-review tests | IMPLEMENTED — UNVERIFIED externally | No Gemini call |
| CX-005 | `apps/web` | Next.js 15.5.29 build exit 0 | VERIFIED build | Authenticated UI E2E not run |
| CX-006 | Login layout | Cloud browser accessibility tree + screenshot inspection | VERIFIED visible render | Screenshot not included as a fabricated product success receipt |
| CX-007 | `database/versions/0001_initial.py` | Alembic upgrade exit 0 | VERIFIED SQLite | PostgreSQL not executed |
| CX-008 | `compose.yaml`, Dockerfiles | Written and inspected | IMPLEMENTED — UNVERIFIED | Docker absent |
| CX-009 | Completion regression guard | `test_completed_payment_cannot_regress` | VERIFIED with provider double | Provider delivery semantics still need real test |
| CX-010 | `docs/` and README | Claim-by-claim self-review | VERIFIED as documentation review | Not independent security audit |
| CX-011 | Public deployment / competition entry | No external write | BLOCKED / not performed | No target host/repository/account access selected |
| CX-012 | Initial live localhost HTTP probe | SOCKS dependency error, then connection refused | FAILED | Process lifetime required repair |
| CX-013 | Real HTTP smoke | `http-smoke.json`: 200 health, 4500/5000 comparison, 409 fixture authorization | VERIFIED | Fixture AI; no external services |

No real keys, payer identities, payment account details or OAuth tokens are included in receipts. Test provider identifiers use TEST prefixes.


## Phase 2 receipts

| ID | Operation | Observed evidence | Status | Limit |
|---|---|---|---|---|
| CX-014 | Report parsers and import endpoint | Parser and workflow tests; raw original reports retained | VERIFIED locally | Source authenticity still human-attested |
| CX-015 | GET-only interrupted-payment recovery | Client-role, grace-period, amount and capture-lock tests | VERIFIED with doubles | Actual PayPal acceptance remains open |
| CX-016 | Historical passport replay | API and exported-file CLI checks in HTTP smoke | VERIFIED locally | Internal consistency only |
| CX-017 | Contract forms and report-upload UI | Phase 2 Next.js production build and type checks pass | VERIFIED build | Authenticated browser E2E not run |
| CX-018 | Complete Phase 2 suite | `junit-phase2.xml`: 89 passed | VERIFIED locally | SQLite / explicit provider doubles |
| CX-019 | Statement coverage and real report parse | 699/755; parser recomputed same coverage | VERIFIED locally | Not branch coverage, AI accuracy or API success |
| CX-020 | Streaming body cap and graph namespacing | Dedicated tests pass | VERIFIED locally | No claim of perimeter DDoS protection |

The resumed runtime initially lacked installed Python packages; a coverage invocation failed before collection. Pinned dependencies were restored and the final complete suite passed. No failure was counted as a passing test.
