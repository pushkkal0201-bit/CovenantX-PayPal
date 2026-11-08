# Submission readiness

**Not ready to claim complete.** This package is a tested development slice with external-service acceptance still open.

| Gate | Status | Evidence / blocker |
|---|---|---|
| A Product | Partial | API workflow tests and frontend build pass; authenticated browser E2E pending |
| B AI | Implemented, unverified | Sequential Gemini adapters exist; key/model absent |
| C Financial correctness | Verified for tested cases | Decimal rules, approval/invalidation, concurrency and state tests |
| D PayPal | Blocked | No real sandbox order, buyer approval, capture or signed webhook receipt |
| E Security | Partial | Implemented critical control tests pass; public deployment hardening remains |
| F Persistence | Verified SQLite | Restart test and migration pass; PostgreSQL unverified |
| G Reproducibility | Partial | Requirements, npm lock, launchers and Compose provided; independent clean-host run pending |
| H Presentation | Partial | Interface, fixture scenario and script provided; full genuine provider demo cannot yet be recorded |
| I Claims | Reviewed | README and draft distinguish verified, simulated and blocked work |

## Next acceptance steps

1. Configure authorized Gemini key/model and PayPal Sandbox merchant credentials locally.
2. Use a real contract and delivery report, inspect source authenticity and run Gemini. Preserve output receipts and evaluate failure cases.
3. Approve one eligible decision, create one sandbox order, complete sandbox buyer approval, capture and GET-reconcile. Record order/capture IDs, not credentials.
4. Register webhook URL and verify real signed events, retries and deduplication.
5. Run Compose with PostgreSQL; exercise restart and simultaneous-payment tests against it.
6. Test client and vendor flows in the browser, including errors and mobile layout.
7. Confirm competition eligibility, publish the correct source repository under MIT, and record a truthful video under three minutes. No entry is automatically submitted.

Phase 2 adds parsed-report ingestion, form-based draft editing, GET-only payment recovery and offline policy replay. These improve the local workflow; the external provider, PostgreSQL and authenticated-browser gates above remain open.

A static preview, a mocked capture or a passing unit test is not a replacement for these gates.
