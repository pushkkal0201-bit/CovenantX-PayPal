# Phase 5 — Inspectable AI review

The Verification workspace now displays stored review stages side by side, with clause selection, a filter for different or missing verdicts, reviewer concerns, expandable quotations and provider receipt identifiers. Exact quotation membership is checked against the submitted text for display; this is not source authentication. The final server assessment still controls eligibility. The same model performs sequential stages and the second receives the first output; the UI does not claim independent agents.

Fixture and legacy records without stage receipts have an explicit empty state. Selecting a different milestone or refreshing to a new revision clears prior graph, scenario and replay results so stale derived views cannot be shown as current.

No new model or PayPal calls are introduced. Real external-service acceptance remains pending configured credentials and a genuine sandbox run.

Validation: production Next.js build passed; TypeScript check passed after the final filter-key adjustment. Authenticated browser interaction and real Gemini execution were not exercised in this increment.
