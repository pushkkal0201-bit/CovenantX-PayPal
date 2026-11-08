# Technology decisions

1. **Modular monolith:** bounded domain functions, persistence, AI and payment adapters under one FastAPI application. An async provider call does not require an unverified distributed queue.
2. **Requested frontend stack:** Next.js 15, React, TypeScript, Tailwind 4, Lucide, TanStack Query, Zod and Framer Motion. Custom native controls are used; shadcn/ui is not integrated. Motion respects reduced-motion preference.
3. **SQLAlchemy aggregate:** a milestone's state and audit insertion commit together with a version predicate. A competing write receives 409. SQLAlchemy uses a synchronous engine; small DB calls execute inside async payment endpoints. This is acceptable for the tested local workload, not a latency/scaling claim.
4. **SQLite local / PostgreSQL Compose:** SQLite enables reproducible tests without Docker. Alembic defines shared relational tables. PostgreSQL deployment and concurrency remain unverified.
5. **USD only:** Decimal inputs with at most two monetary fractional digits. No unsupported currency exponent assumptions. Full deduction totals cannot exceed the base value.
6. **Human-approved structured rules:** source text is retained, but natural-language financial obligations are not auto-binding. PDF extraction and a draft Contract Agent are deferred.
7. **Two sequential reviewer stages:** Google GenAI technical mapping and adversarial review use one configured model. They are not independent services or independent statistical judges. No hidden chain-of-thought is stored.
8. **Human-attested provenance:** commit association, timestamp and content hashes can detect specific mismatches. They cannot prove that the supplied report came from a real CI run. Client inspection is required.
9. **No payment simulation in runtime:** test doubles are confined to tests. Fixture verification is visible and cannot approve settlement. External integration failure produces a blocked or uncertain state.
10. **Read-only counterfactual:** a copied evidence object changes coverage for the simulation. The endpoint never calls persistence or a payment provider.
11. **Deployment deferred:** this requested Python/PostgreSQL stack cannot run directly on the available Worker/static hosting surface. Render was discoverable but not connected. No substitute static page is presented as a working hosted financial application.
12. **Sponsor restraint:** AG Grid was considered, but the small clause matrix is implemented with a semantic HTML table. Enterprise grid licensing was not assumed. See sponsor decisions.

13. **Bounded report parsers:** derive statement coverage, read k6 latency aggregates and classify explicitly scored SARIF results. Unsupported or ambiguous reports fail closed. Upload origin remains human-attested.
14. **GET-only recovery:** candidate order IDs are untrusted lookup hints. The server checks the original approval snapshot and amount before persistence; no recovery operation moves funds.
15. **Historical replay:** deterministic checks use the stored verification time rather than today, avoiding false replay failures when evidence ages. Digest checks establish consistency, not authorship.
16. **Compatibility:** new aggregate fields are optional; no new relational migration. Old uncertain payment records remain capture-blocked.
