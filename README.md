# CovenantX

**Software delivery review · Contract deductions · PayPal Sandbox checkout**

[Problem](#the-problem) · [Example](#a-worked-example) · [Workflow](#how-a-milestone-moves-through-the-app) · [Architecture](#architecture) · [Workspace](#workspace) · [Setup](#run-covenantx-locally) · [Sample](#run-the-sample)

CovenantX connects software acceptance criteria to a milestone payment. A client agrees on delivery rules, a vendor submits the reports, and Gemini reviews the evidence. The server applies the agreed deductions and prepares an amount for the client to approve through PayPal Sandbox.

## The problem

A failed acceptance check has a financial consequence only if the contract says what that consequence is. In practice, the terms, test reports and payment record often sit in different places. Working out a deduction means finding the right report, checking which delivery it belongs to and matching the result to the original agreement.

CovenantX keeps those records together. Each finding points to a contract clause and a quotation from the submitted evidence. Each payment refers to the settlement snapshot the client approved.

It's intended for software delivery milestones with measurable acceptance criteria, such as coverage targets, response-time limits, security findings or required documentation. The client and vendor agree on the rules before the delivery is reviewed.

## A worked example

Suppose a milestone is worth $5,000. Its contract requires at least 85% statement coverage, with a $500 deduction for falling below that threshold.

The vendor submits a report showing 78%. The client checks the report's source and commit, then requests a review. If the remaining clauses pass and the evidence checks clear, CovenantX proposes $4,500. The client can open the coverage finding, inspect the supporting text and approve the amount before creating a PayPal Sandbox order.

<details>
<summary><strong>Open the sample contract and deduction breakdown</strong></summary>

| Clause | Agreed requirement | Submitted measurement | Result | Deduction |
| --- | --- | --- | --- | --- |
| Coverage | At least 85% statement coverage | 78% | Fail | $500 |
| Latency | P95 at most 200 ms | 180 ms | Pass | $0 |
| Security | Zero critical findings | 0 | Pass | $0 |
| Documentation | Delivery documentation present | Present | Pass | $0 |

**Proposed amount = $5,000 − $500 = $4,500**

Changing the hypothetical coverage to 90% in Settlement studio produces a $5,000 comparison. The saved proposal keeps its original evidence and amount. A different payable decision requires evidence review and client approval.

</details>

## How a milestone moves through the app

```mermaid
flowchart TD
    Contract["Client approves the milestone terms"] --> Evidence["Vendor submits reports for the delivery commit"]
    Evidence --> Attest["Client inspects and attests the evidence"]
    Attest --> Review["Gemini reviews the evidence in two stages"]
    Review --> Gate{"Do the findings pass the evidence checks?"}
    Gate -->|No| Hold["Hold settlement for review"]
    Gate -->|Yes| Calculate["Apply agreed deductions in USD"]
    Calculate --> Approve["Client approves the settlement snapshot"]
    Approve --> Checkout["Buyer approves the PayPal Sandbox order"]
    Checkout --> Capture["Client captures and reconciles the order"]
```

The workflow has three approval points. The client first approves the contract, then attests the submitted evidence, and finally approves the settlement amount. These are separate actions because they answer different questions: what was agreed, what was delivered and what should be paid.

### Contract and evidence

Each contract clause defines a metric, comparison, threshold and deduction. Approval freezes those rules. Reports are associated with the delivery commit, and the API stores their content, hashes and parsed measurements.

The client records how they inspected the source and measurements. Hashes let the application identify the submitted content. Source inspection depends on the client's attestation.

### Gemini review

The first Gemini call assesses the evidence against the clauses. The second receives that assessment and checks it for unsupported conclusions or contradictions. Both stages use the configured model, and their findings and quotations are available in the Verification workspace.

The API checks that every approved clause has a finding, that each quotation occurs in the evidence and that the verdict agrees with the supplied measurement. It also checks the delivery commit, report age and required measurements. An unresolved concern or failed check puts the proposal on hold.

### Settlement and checkout

For each failed clause, the server subtracts the deduction written into the approved contract. Calculations use decimal arithmetic in USD. The client reviews the result and approves a snapshot tying the contract, evidence and decision to the payment.

CovenantX uses that amount to create a PayPal Sandbox order. After the buyer approves it in PayPal, the client requests capture and reconciliation. The API checks the returned order, currency, amount and snapshot reference before recording completion. Stored request IDs and payment states control retries when a response is interrupted.

## Architecture

The web app talks to a FastAPI service through the Next.js API proxy. FastAPI owns milestone state, evidence parsing, review checks and payment operations. Provider credentials stay in the backend environment.

```mermaid
flowchart TD
    Browser["Client or vendor workspace"] --> Proxy["Next.js API proxy"]
    Proxy --> API["FastAPI role and revision checks"]
    API --> Store["SQLAlchemy milestone and audit store"]
    API --> Parse["Report parsers"]
    Parse --> Review["Gemini review"]
    Review --> Policy["Citation checks and settlement policy"]
    Policy --> Store
    API --> Payments["PayPal adapter"]
    Payments --> Sandbox["PayPal Sandbox"]
    Sandbox --> Verify["Order and capture validation"]
    Verify --> Store
```

<details>
<summary><strong>How review results become a payable amount</strong></summary>

Gemini receives the approved contract and submitted evidence as structured input. Each stage returns clause IDs, verdicts, exact quotations and explanations. The saved stage records include the input digest and provider response ID when available.

The second stage sees the first stage's findings. If their verdicts disagree, the review records a concern. A concern from the first stage is preserved even if the second stage clears its own concern.

The server then checks the assessment against the contract and evidence.

| Check | What it establishes |
| --- | --- |
| Clause coverage | Every approved clause appears exactly once in the assessment. |
| Exact quotation | The cited text occurs in the submitted evidence. |
| Numerical agreement | The verdict agrees with the clause's comparison and measured value. |
| Commit match | The evidence refers to the approved delivery commit. |
| Observation time | The evidence falls within the accepted freshness window. |
| Review concerns | Unresolved interpretation problems hold the proposal for inspection. |

The final amount is calculated from the deductions already recorded in the approved contract. A zero-value proposal is held because it cannot be submitted as a checkout order.

</details>

<details>
<summary><strong>What happens when two actions reach the same milestone</strong></summary>

Each update includes the revision the caller read. The database update succeeds only if that revision still matches. A stale action receives a conflict response and the user refreshes before acting.

A successful write saves the milestone and its audit event in the same transaction. The event records the acting role, time, revision, state transition and names of changed fields. Payment creation and capture also claim their state before calling PayPal.

</details>

### Payment sequence

```mermaid
sequenceDiagram
    participant Client
    participant API as CovenantX API
    participant PayPal as PayPal Sandbox
    Client->>API: Approve the settlement snapshot
    API-->>Client: Store approval
    Client->>API: Create order
    API->>PayPal: Submit approved USD amount and request ID
    PayPal-->>API: Order ID and buyer approval URL
    API-->>Client: Open PayPal approval
    Client->>PayPal: Sign in as Sandbox buyer and approve
    Client->>API: Capture approved order
    API->>PayPal: Capture with stored request ID
    PayPal-->>API: Capture response
    API->>API: Validate order, snapshot, amount and capture
    Client->>API: Reconcile provider
    API->>PayPal: Read order
    PayPal-->>API: Current order and capture status
    API-->>Client: Validated payment status
```

The configured Sandbox merchant receives the payment. The client and vendor tokens control workspace actions, while PayPal buyer approval takes place in the Sandbox checkout.

<details>
<summary><strong>Interrupted requests and reconciliation</strong></summary>

A network error can leave the application uncertain about the provider's result. CovenantX records that uncertainty in the payment state and keeps the original payment identifiers.

Reconciliation reads the existing order from PayPal and validates it against the approved snapshot. The recovery action can also inspect a candidate order after an interrupted operation. It checks the milestone reference, snapshot reference, currency and amount before adopting the provider result.

Webhook processing sends the delivery headers and payload to PayPal for signature verification. It uses the registered webhook ID and records event IDs to handle repeated deliveries.

</details>

## Evidence the app accepts

| Evidence | Measurement used in the contract |
| --- | --- |
| Coverage.py JSON | Statement coverage calculated from the report's counts |
| k6 custom summary JSON | P95 HTTP request duration from the summary |
| SARIF security report | Count of critical findings from the supported SARIF fields |
| Plain text or Markdown | Presence of a nonempty document. The client reviews its completeness. |

The contract determines which measurements are required. A milestone with a single documentation clause can be reviewed using its delivery document alone.

## Workspace

| Workspace | What you can inspect or do |
| --- | --- |
| Overview | Follow the active milestone and see how deductions affect the proposed payment. |
| Contract & evidence | Set the rules, upload delivery reports and record client attestation. |
| Verification | Compare the two Gemini review stages and expand the exact evidence quotes. |
| Settlement studio | Inspect the amount by clause, try a hypothetical coverage value and approve the stored proposal. |
| CovenantGraph | Follow the links between a clause, its evidence and its finding. |
| Disputes | Raise a dispute and record the vendor's resolution. Settlement requires fresh client approval after resolution. |
| PayPal operations | Create the Sandbox order, open buyer approval, capture and reconcile. |
| Evidence passport | Export the decision record and replay its stored policy calculation. |
| Activity log | Filter or export events by role and inspect recorded state transitions. |

### Inspecting the result

The interface keeps the active milestone selected as you move between workspaces. From Overview, each journey step opens the relevant workspace.

- **Review findings** can be filtered by clause or by differences between the two stages. Expand a finding to read its source quotation.
- **Settlement comparisons** let you change a hypothetical coverage value and inspect the effect on the amount.
- **Activity history** can be searched and filtered by actor role, then exported as JSON.
- **Evidence passports** collect the contract, evidence, decision and payment information for the selected milestone.

<details>
<summary><strong>Check an exported evidence passport</strong></summary>

From the repository root, run:

```bash
python scripts/passport.py downloaded-passport.json --replay --report passport-report.md
```

The command checks the retained digest, replays the stored policy calculation and writes a readable report. Digest verification establishes consistency with the retained hash. Source authenticity depends on the evidence inspection recorded by the client.

</details>

## Stack

| Layer | Tools and responsibilities |
| --- | --- |
| Web | Next.js, React and TypeScript for the workspace. TanStack Query handles API reads and polling. |
| API | Python, FastAPI and Pydantic handle role checks, input validation and milestone operations. |
| Storage | SQLAlchemy stores milestones and audit events. SQLite is the default for local use. Docker Compose uses PostgreSQL, with Alembic for schema migrations. |
| Review | The Google GenAI SDK makes two sequential Gemini calls. Python checks citations and applies the contract rules with decimal arithmetic. |
| Payments | PayPal Sandbox Orders API handles approval and capture. Stored request IDs support safe retries, and reconciliation checks the provider's order against the approved snapshot. |

<details>
<summary><strong>Repository guide</strong></summary>

| Path | Responsibility |
| --- | --- |
| `apps/web/app/` | Page composition, navigation and workspace actions |
| `apps/web/components/` | Contract editor, report importer, review inspection and activity history |
| `apps/api/covenantx/main.py` | API routes and milestone transitions |
| `apps/api/covenantx/domain.py` | Input contracts, evidence checks and settlement arithmetic |
| `apps/api/covenantx/ai.py` | Gemini requests and sequential review records |
| `apps/api/covenantx/artifacts.py` | Report parsing and measurement receipts |
| `apps/api/covenantx/paypal.py` | OAuth, orders, capture, signature verification and response validation |
| `apps/api/covenantx/store.py` | Revision checks, persistence and audit writes |
| `database/` | Database migrations |
| `scripts/` | Configuration, startup and passport commands |
| `demo/` | Sample contracts, reports and request collection |
| `tests/` | Backend behavior and integration checks |

</details>

The workspace uses one client token and one vendor token per deployment. Checkout uses the Sandbox merchant tied to the configured PayPal app, and all milestone amounts are in USD.

## Run CovenantX locally

Create a Python virtual environment, install the backend requirements and generate the local `.env` from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/configure_local.py
python scripts/run_api.py
```

Use the [local runbook](docs/LOCAL_RUNBOOK.md) for Windows Command Prompt commands, runtime prerequisites, Sandbox credentials and troubleshooting. Run the web app in a second terminal:

```bash
cd apps/web
npm ci
npm run dev
```

Open [CovenantX](http://localhost:3000) and unlock with the client or vendor token from your local `.env`. The [API health endpoint](http://127.0.0.1:8000/api/health) shows whether the provider settings loaded.

## Run the sample

The repository includes a $5,000 sample contract and fictional delivery evidence.

1. Unlock as the client, create the prefilled draft and approve its contract.
2. Switch to the vendor. Open **Advanced manual evidence / fixture** and submit the prefilled evidence.
3. Switch back to the client, inspect the sample and record an attestation.
4. In **Verification**, click **Run labeled fixture**.
5. Open **Settlement studio**. The sample produces a $500 coverage deduction and a $4,500 proposal.

Fixture results are labeled simulated and cannot authorize payment. This gives you a repeatable way to inspect the clauses, calculations and evidence passport.

To exercise Gemini and PayPal Sandbox, use a fresh milestone with actual evidence from its delivery commit. The [local runbook](docs/LOCAL_RUNBOOK.md#test-gemini-and-paypal-sandbox) covers a documentation milestone using this repository's README, including buyer approval, capture and reconciliation.

[Architecture](docs/ARCHITECTURE.md) · [PayPal integration](docs/integrations/PAYPAL_INTEGRATION.md) · [Threat model](docs/security/THREAT_MODEL.md) · [MIT License](LICENSE)
