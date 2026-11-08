# Architecture

The implementation stores one versioned milestone aggregate plus separate audit and webhook-event tables. There is no external graph database, agent scheduler, queue or vector store.

## System context

```mermaid
flowchart TD
  Vendor["Agency vendor"] --> Web["CovenantX web workspace"]
  Client["Business client"] --> Web
  Web --> API["Authorized FastAPI endpoints"]
  API --> Gemini["Gemini review provider"]
  API --> PayPal["PayPal Sandbox"]
  API --> Store["SQLite or PostgreSQL"]
```

## Implemented components

```mermaid
flowchart TD
  Main["main.py: role and state checks"] --> Domain["domain.py: contracts, trust, settlement"]
  Main --> Store["store.py: atomic revision and audit write"]
  Main --> AI["ai.py: structured review calls"]
  Main --> Provider["paypal.py: OAuth and Orders v2"]
  Domain --> Passport["canonical JSON / SHA-256"]
```

## AI orchestration

```mermaid
flowchart TD
  Inputs["Approved clauses + attested evidence"] --> Technical["Technical and SLA reviewer"]
  Technical --> Adversarial["Adversarial reviewer, same configured model"]
  Adversarial --> Gate{"Complete, grounded and consistent?"}
  Gate -->|No| Held["Hold and request review"]
  Gate -->|Yes| Proposal["Deterministic proposal, awaiting client"]
```

A typed Assessment is the output contract. Every finding needs an approved clause ID, pass/fail/unknown verdict, exact source quote and explanation. Missing IDs, duplicated IDs, unknown findings, absent citations, conflicts with attested metrics and reviewer concerns block eligibility. None of these controls establishes statistical accuracy or immunity to prompt injection.

## Financial state machine

```mermaid
stateDiagram-v2
  [*] --> DRAFT
  DRAFT --> AWAITING_EVIDENCE: client freezes rules
  AWAITING_EVIDENCE --> EVIDENCE_SUBMITTED: vendor submission
  EVIDENCE_SUBMITTED --> EVIDENCE_ATTESTED: client inspection
  EVIDENCE_ATTESTED --> PROPOSED: grounded review
  EVIDENCE_ATTESTED --> HELD: insufficient evidence
  PROPOSED --> DISPUTED: either party challenges
  DISPUTED --> PROPOSED: vendor resolves, proposal remains eligible
  PROPOSED --> APPROVED: fresh client snapshot approval
  APPROVED --> CREATING: atomic revision claim
  CREATING --> ORDER_CREATED: validated provider order
  CREATING --> CREATE_UNKNOWN: request uncertainty
  CREATE_UNKNOWN --> CREATING: same key within bounded window
  ORDER_CREATED --> CAPTURING: client requests capture
  CAPTURING --> ORDER_CREATED: payer has not approved
  CAPTURING --> CAPTURE_UNKNOWN: uncertainty or pending
  CAPTURING --> COMPLETED: matching completed capture
  CAPTURE_UNKNOWN --> COMPLETED: GET confirms capture
  COMPLETED --> [*]
```

PROVIDER_REVIEW is used for unfamiliar provider states. Before payment starts, new evidence invalidates verification, proposal and approval. Open disputes independently block settlement approval even if a subsequent verification returns PROPOSED. Payment states lock evidence and dispute mutation. A completed record cannot regress to a capture-eligible state.

## Evidence provenance

```mermaid
flowchart TD
  Text["Original contract text"] --> Rules["Human-approved structured clauses"]
  Artifact["Vendor artifact text + claimed metadata"] --> Hash["Canonical evidence hash"]
  Hash --> Attest["Client inspection note bound to hash"]
  Rules --> Findings["Quoted findings"]
  Attest --> Findings
  Findings --> Proposal["Rule-derived deductions"]
  Proposal --> Passport["Exported record and audit digest"]
```

CovenantGraph is a derived relationship view over these stored records. It supports inspection, not a graph-query language. Artifact authenticity remains human-attested.

## Storage

```mermaid
erDiagram
  MILESTONES ||--o{ AUDIT_EVENTS : "application association"
  MILESTONES {
    string id PK
    int version
    text data
  }
  AUDIT_EVENTS {
    string id PK
    string milestone_id
    text data
  }
  WEBHOOK_EVENTS {
    string id PK
    string received_at
  }
```

The audit association is indexed, not a database foreign key. Audit events contain actor, timestamp, event, version and record hash. There is no write endpoint for audit rows, but a database administrator can modify them; there is no append-only storage guarantee. Backups, encryption at rest and administrative audit controls belong to deployment and have not been configured.


## Phase 2 extensions

`artifacts.py` parses original uploaded report text into derived evidence and per-file receipts. The vendor import endpoint persists the original bundle, derived evidence and provenance together, invalidating previous verification and approvals. `middleware.py` bounds streamed request bodies before parsing. The client can edit a DRAFT with a revision-bound contract endpoint; approved terms remain immutable.

`replay.py` reconstructs evidence from saved artifacts and recalculates settlement at the recorded verification timestamp. Both the authenticated API and offline passport CLI use it. It does not call Gemini, PayPal or a network source.

The recovery endpoint accepts an explicit order ID and note only for uncertain/interrupted states. After a two-minute grace period, it GETs provider state and applies the existing identity, amount, currency and snapshot validation. A record with a submitted capture, or a legacy uncertain provider-review state, cannot become capturable through recovery.
