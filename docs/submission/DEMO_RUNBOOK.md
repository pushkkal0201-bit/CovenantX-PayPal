# Demo runbook

## Offline/integration-test proof

Run `python -m pytest -q`. This executes labeled provider doubles. Never show a TEST-ORDER / TEST-CAPTURE receipt as real PayPal success.

## Browser fixture story

Follow README setup. Open the UI as client and create the sample $5,000 milestone. Read and approve its contract. Switch to the vendor token and import the four fictional reports from `demo/reports/` (or submit manual sample evidence). Switch back to client, inspect active evidence and attest the artifact with a note. Run the labeled fixture review. Show the 78% coverage violation, $500 deduction and $4,500 proposal. Compare 90% coverage in the hypothetical simulator; show $5,000 without changing the live proposal. Inspect graph edges, replay the stored decision, and export the passport. Demonstrate that payment approval fails for fixture evidence.

## Real sandbox acceptance

Use your own genuine report and a new intended milestone; do not relabel the fictional fixture as real. Supply the correct commit SHA, recent timestamp, metrics and report text. Human attestation is a source inspection statement, not a cryptographic proof. Run Gemini, inspect citations and resolve every hold. If the model fails, stop: do not switch to a fixture and call it AI.

Approve the settlement and create one sandbox order. Open its PayPal payer-action link, use your sandbox buyer account, approve, then return and request capture. Reconcile. Confirm the provider status is COMPLETED and a capture ID is stored. Export the passport. If uncertain, use reconciliation and inspect the provider; after an interruption, the recovery action can GET and validate a candidate order, but cannot create or capture it; never create duplicate milestones to force a retry.

## Video script (target 170 seconds)

- 0–20: “A delivery SLA and its payment often live in different systems. CovenantX shows why a milestone payment has this amount.”
- 20–50: Show agreed clauses and actual report provenance. Explain human attestation honestly.
- 50–85: Show completed Gemini findings and their exact source quotes **only after a real call succeeds**. Otherwise label fixture mode and say AI execution remains pending.
- 85–115: Show $4,500 proposal, then the 90% hypothetical comparison at $5,000. Explain that this does not modify a payable record.
- 115–150: Show actual sandbox approval/capture/reconciliation **only after acceptance succeeds**. If blocked, show disabled/blocked state and disclose the missing integration instead of splicing a fake receipt.
- 150–170: Export passport and state the implemented scope and remaining limitations.

Do not submit the blocked version as a completed integrated demo. The acceptance plan identifies the remaining work; it does not supply a real transaction or recorded video.
