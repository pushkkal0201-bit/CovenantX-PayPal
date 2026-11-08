# CovenantX — Evidence-backed milestone assurance

**Working draft; not submitted. External integration acceptance must be completed before claiming a finished PayPal + AI project.**

## Inspiration

A software milestone can have acceptance criteria in a contract, test evidence in a delivery report, and its final payment in a separate finance tool. We wanted to make the deduction and the evidence behind it inspectable by both parties.

## What it does

CovenantX stores human-approved financial rules and vendor evidence. A client attests the source and measurements. The system interprets each clause, checks citations and numeric consistency, calculates the agreed deductions, and requests explicit client approval of the resulting decision. Its counterfactual view shows how improving evidence would change payment without mutating the approved record. An Evidence Passport exports the inputs, findings, approvals and provider identifiers.

## How it was built

Next.js 15, TypeScript and TanStack Query provide the workspace. FastAPI, Pydantic, SQLAlchemy and Alembic provide typed APIs and revision-controlled persistence. The Google GenAI adapter performs sequential technical and adversarial reviews. A sandbox-only HTTPX adapter implements PayPal OAuth and Orders v2, with durable request IDs and reconciliation. Decimal arithmetic supplies payment amounts from approved rules.

## Demonstrated achievements

The local suite passed 89 tests covering authorization, stale approvals, contradictory evidence, financial boundaries, disputes, uncertain provider results, replay handling, persistence and passport integrity. Phase 2 adds report parsing, historical decision replay and GET-only recovery checks. The backend statement-coverage result is 699/755 (92.58%); this is not an AI accuracy or live-integration claim. The production frontend build and local SQLite migration succeeded. The login layout was inspected in a browser.

## Challenges

An uncertain payment request cannot safely be treated as a failed payment. We preserve uncertain states and reconcile rather than issue a new payment. A plausible-looking evidence report also cannot authenticate itself: this version explicitly requires human attestation and makes no independent CI provenance claim.

## Current limitations

Real Gemini execution and PayPal Sandbox payment have not yet been completed in this build environment. Provider tests use labeled doubles. PostgreSQL/containers and authenticated browser E2E remain unverified. PDF ingestion, GitHub artifact retrieval, individual user identity, refunds and public hosting remain future work.

## Next work

Complete actual model and sandbox acceptance; evaluate adversarial artifact cases; add authenticated CI collection; test PostgreSQL contention and interrupted-operation recovery. Expand the product only after the core workflow is independently reproducible.
