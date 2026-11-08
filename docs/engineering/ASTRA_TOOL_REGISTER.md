# Actual tool capability register

Observed 2026-11-08 IST. Availability is not evidence of successful external integration.

| Capability | Actual tool | Access verified | Permission / scope | Intended operation | Status |
|---|---|---|---|---|---|
| Local code execution | exec_command / Python / Node | Yes | Workspace execution | Build, migration, tests | Available; executed |
| File edits | Shell writes | Yes | New project directory | Source generation | Available; executed |
| GitHub search | Connected GitHub search_repositories | Yes | Read search | Locate CovenantX source | Available; no matching repo found |
| GitHub write | Connector methods exposed | No write performed | No target repo established | Source management | Not used |
| API context | Web search, official PayPal/Google docs | Yes | Public docs | Implement adapter contracts | Available; read |
| Browser | cua_repl cloud browser | Yes | Local preview QA | Inspect rendered login page | Available; login layout verified only |
| App preview | sites-preview | Yes after flag repair | Internal preview | Run Next.js | Available; not deployment |
| Artifact persistence | Library create file | Recorded at final save | New source ZIP | Deliver package | See successful final save |
| APIMatic | Plugin search | No matching plugin found | No connection made | API context | Blocked/not used; official docs used |
| Render | Plugin discovery | Listed, not installed | No account connected | Host Python/PostgreSQL | Not connected / not deployed |
| Sites hosting | Sites tool exposed | No deployment attempted | Worker/static hosting | Cannot directly host this Python stack | Not used |
| PayPal | HTTPX adapter | No authenticated provider call | Sandbox only | Order/capture/reconcile | Blocked: credentials absent |
| Gemini | Google GenAI SDK import | SDK installed | Model call requires account | Grounded review | Blocked: API key/model configuration absent |
| Docker | Executable discovery | No executable found | None | Compose/PostgreSQL verification | Unavailable |
| Subagents | Collaboration API exposed | No delegation performed | Functional roles implemented in code | Optional review | Not used; no independent review claimed |

No new external accounts, paid resources, public deployments, production payments or competition submissions were performed.
