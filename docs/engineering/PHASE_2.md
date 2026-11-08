# Phase 2 — Report ingestion, recovery and decision replay

This update extends the first development release. Existing milestone records remain readable: new data is stored in optional aggregate fields, so no new relational migration is required. The original application remains a single client/vendor workspace.

## Implemented changes

1. **Report ingestion.** Coverage.py, k6 summary, a bounded SARIF 2.1 subset and text documentation can be uploaded. Measurements are derived server-side and original content is retained. Contradictory or unsupported reports fail without altering the previous approved record.
2. **Contract editor.** The UI now has labeled fields for title, amount, commit, source terms, metrics, comparison operators, thresholds and deductions. Drafts can be edited with a revision-bound endpoint. Approved rules remain immutable.
3. **Evidence inspection.** Uploaded-file receipts expose hashes, format and derived measurements. Human attestation remains required because parser success does not prove source authenticity.
4. **Payment recovery.** After a two-minute grace period, the client may supply a candidate sandbox order ID and inspection note. Recovery only GETs provider state; it validates the original amount, milestone and approved snapshot before persisting anything. It cannot create or capture a payment.
5. **Capture uncertainty.** A durable capture-submitted marker prevents a transient or unfamiliar provider state from reopening capture. Legacy records with an uncertain provider-review state also remain blocked.
6. **Policy replay.** Both the UI and CLI can reparse original artifacts, check input bindings and recompute a settlement at its historical verification time. The check makes no model or provider calls. It checks internal consistency, not authenticity.
7. **Request bounds.** An ASGI middleware caps request bodies, including chunked requests. Existing schema bounds and role controls remain in place.
8. **Graph identifiers.** Clause nodes are namespaced to prevent collisions with the contract root.
9. **Reproducibility.** Updated HTTP smoke, offline replay CLI, fixture reports, generated OpenAPI and Postman requests accompany the source.

## Verification

The final executed results are in `docs/evaluations/PHASE_2_TEST_REPORT.md`, with raw outputs next to it. Provider-facing recovery tests use explicit doubles. The HTTP smoke uses a real Uvicorn process and local requests, with fixture review clearly labeled.

## Still open

Real Gemini execution, actual PayPal Sandbox approval/capture and signed webhook delivery require configured credentials. PostgreSQL/container execution, authenticated browser E2E, automated CI source authentication, PDF extraction, public deployment, per-user identity and refunds remain unverified or unimplemented. This phase does not remove those acceptance gates.
