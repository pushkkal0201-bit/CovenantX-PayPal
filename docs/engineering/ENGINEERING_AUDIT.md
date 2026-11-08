# Engineering audit

Research/build date: 2026-11-08 IST.

The supplied attachment was an engineering directive, not source code. Local attachment inspection, two title searches (CovenantX / Covenant) and a GitHub repository search scoped to the user's account did not locate a matching codebase. This does not prove none exists; it establishes that no existing implementation was available to audit in this session. This package is therefore a new implementation. No older ProofPay or VeriPay repository was modified.

## Delivered boundary

A single client/vendor workspace can persist contracts, evidence, findings, disputes and decision records. Test doubles exercise settlement approval through capture. Production runtime adapters have no fallback that converts provider failure into simulated success. Users explicitly select fixture review, and fixture review is prohibited from authorizing payments.

## Skeptical review

| Severity | Finding | Disposition |
|---|---|---|
| Critical release gate | No actual PayPal or Gemini execution receipt | Open; credentials and a real sandbox approval/capture required |
| High | Uploaded report provenance and URLs remain assertions | Report values can now be derived and checked for contradictions; human source attestation remains required |
| High | Deployment tokens identify roles, not individual people | Explicit single-pair prototype; managed per-user identity required before public deployment |
| High | A process crash after claiming payment may leave a locked state | GET-only candidate-order recovery implemented with grace period, snapshot/amount validation and audit note; no automatic capture retry |
| High | Refunds and post-payment disputes are not handled | Explicitly outside this release; no claim of full payment lifecycle |
| Medium | LLM agreement does not establish truth | Exact quote, measurement consistency and concern gates plus human evidence inspection; no accuracy claim |
| Medium | JSON aggregate limits reporting and granular schema constraints | Versioned typed boundary and atomic compare-and-swap; normalized design deferred |
| Medium | Request size guard is not comprehensive perimeter protection | Streamed body cap and field limits implemented; slow-client and perimeter protections remain deployment work |
| Medium | Rate limits are process-local | Documented; distributed gateway limits deferred |
| Medium | Provider failure details are sanitized but not richly classified | Generic actionable uncertainty response; GET-only recovery UI added; richer provider error classification remains future work |
| Low | Default fixture editor is a developer-oriented form | Usable JSON/text ingestion; PDF and polished clause editing deferred |

## Defects found and corrected during this build

- Managed preview passed Vite flags to Next.js. A small launcher translates `--host` to `--hostname` and removes `--strictPort`.
- Added a monotonic completion guard: provider reconciliation cannot reopen a completed transaction for capture.
- Set the Docker web build's internal API URL explicitly because Next.js rewrites are build-sensitive.
- Fixed the test runner's async loop-scope warning with explicit configuration.
- Local HTTP probe inherited an unsupported SOCKS proxy. Localhost probes used direct local transport; dependency declaration now includes HTTPX SOCKS support for configured environments.

No independent human or external-agent review occurred. This is a skeptical self-review backed by the included tests.

Phase 2 changes and validation supersede the initial implementation limitations where explicitly noted in [PHASE_2.md](PHASE_2.md).
