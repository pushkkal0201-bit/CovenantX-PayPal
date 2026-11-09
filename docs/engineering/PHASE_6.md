# Phase 6 — Operational activity history

The Activity log reads authenticated passport audit records and presents newest-first events, actor filters, event/state/field search, revision numbers, timestamps and filtered JSON export. Exports contain event metadata rather than full evidence content. Loading, retry and empty states are explicit.

New audit entries add the previous state, resulting state and names of changed top-level fields. Values are not copied into summaries. These entries are committed in the same database transaction as the optimistic revision update; rejected stale writes do not add an audit entry. Older records require no migration and remain viewable without new metadata.

Shared role tokens identify client/vendor roles, not named individuals. Database operators can modify records; this is not an immutable or independently authenticated ledger. Audit reads currently load a milestone’s complete history through the existing passport endpoint; database pagination remains future scalability work.

Validation: all 94 backend tests passed, including audit authorization, transition summaries and rejection of stale writes. Authenticated browser interaction and real provider acceptance remain unverified.

Frontend validation: Next.js production build and TypeScript checks passed.
