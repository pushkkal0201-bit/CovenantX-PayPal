# Threat model and security limits

Scope: a development deployment for one client/vendor pair, using sandbox payments. Assets: contract terms, uploaded evidence text, role tokens, decision snapshots and payment intent identity.

| Threat | Implemented control | Evidence | Residual limitation |
|---|---|---|---|
| Vendor approves own payment | Separate bearer tokens; server-side client role | Role boundary tests | Shared tokens lack individual identity and revocation history |
| Browser substitutes amount | Payment endpoint accepts revision only; amount loaded from DB | Extra-field validation and provider adapter tests | Database admin can alter aggregate |
| Model invents penalties | Model schema contains no amount; only approved rules calculate money | Domain tests | Human may approve an erroneous rule |
| Invented source support | Exact quote required; attested metrics cross-checked | Hallucination/contradiction tests | A fabricated vendor artifact can still contain plausible quotes and consistent report counts |
| Prompt injection | Untrusted-data instructions, typed output, no tools, reviewer concern gate | Deterministic concern rejection test | No live adversarial model benchmark; not injection-proof |
| Stale approval | Expected revision and immutable approval snapshot | Stale-write and concurrent approval tests | Expired or revised contracts require operational management |
| Duplicate click / concurrent action | Atomic DB revision claim before provider call, durable keys | Workflow tests | Cross-milestone duplicate business obligations not automatically detected |
| Capture timeout | CAPTURE_UNKNOWN blocks recapture; GET reconciliation | Timeout test | Manual intervention may be necessary indefinitely |
| Webhook forgery / replay | Provider signature endpoint; event ID storage; GET reconciliation | Provider doubles | Actual signed delivery not tested |
| Malicious artifact URL / SSRF | User source URLs are stored, not fetched; PayPal base fixed | Source inspection | Future collector must add origin/redirect/private-network restrictions |
| XSS in artifact text | React text rendering; no dangerous HTML injection | Source inspection; login rendering only | Authenticated UI requires browser regression tests |
| Token exposure | UI memory only, no token logs, `.env` ignored | Source inspection | No full CSP and no hardened shared-host deployment |
| Resource exhaustion | Input field bounds; per-role local limits; streamed 1 MB body cap | Source inspection | Unauthenticated floods and slow-client protection still need gateway controls |
| Passport tampering | Canonical SHA-256 and offline comparison | Integrity test | No signature; attacker replacing payload and digest is not detected |

## Release blockers

Do not deploy this as a public multi-tenant financial application. Add managed per-user identity, resource ownership rules, comprehensive request limits, broader operational recovery beyond candidate-order GET, signed/independently collected evidence, PostgreSQL contention tests, live provider verification, backups, webhook routing and refund/dispute operations first. This is a concrete scope limitation, not a compliance opinion.

## Secret handling

Use locally generated random role tokens. Keep API credentials only in server environment variables. Never place Gemini or PayPal secrets in `NEXT_PUBLIC_*`. The provider URL cannot be changed to a production host by configuration. Rotate any real secret accidentally committed and remove it from history.

Phase 2 adds a read-only provider recovery action and offline settlement replay. These were tested locally with explicit provider doubles. Recovery cannot create/capture transactions; replay cannot authenticate reports or independently confirm a model/payment event.
