# Artifact import and assurance

Phase 2 adds `POST /api/milestones/{id}/evidence/import?version={version}` for vendor access. The JSON body contains a commit SHA, artifact reference, source URL, observation timestamp, demonstration flag and one or more `{name, format, content}` objects. The UI reads selected files as text and sends this same envelope. It does not execute files, unpack archives or fetch the source URL.

Original UTF-8 content, per-file SHA-256, parser version and derived measurements are retained in the milestone and passport. Successful parsing does **not** authenticate the scanner, source repository, claimed commit or timestamp. Client inspection remains mandatory.

## Supported subset

| Format | Derived metric | Validation and interpretation |
|---|---|---|
| `coverage-py-json` | `coverage` | Statement coverage: sum covered lines / sum statements × 100. Per-file counts must reconcile and match totals. Zero statements are rejected. Explicit statement percentages must agree within 0.01 percentage points. Combined branch-and-line percentages are not substituted for statement coverage. |
| `k6-summary-json` | `p95_ms` | Requires `metrics.http_req_duration` as a time trend, its `values.p(95)`, min/max and a positive HTTP request count. P95 must lie within min/max. This reads an uploaded aggregate; it does not reconstruct a percentile from raw samples. |
| `sarif-2.1-json` | `critical_count` | Requires declared security rules, successful invocation metadata and explicit results. A rule's numeric `security-severity >= 9.0` is critical under this project's documented policy. Unknown rules, nonfinite values, contradictory execution status, external properties, ambiguous suppressions and baseline-absent findings are rejected for manual interpretation. |
| `documentation-text` | `documentation` | A nonempty text document derives presence = 1. This does not establish completeness or technical quality; the reviewer sees a bounded excerpt. |

Unsupported schemas are rejected instead of converted to zero findings or passing evidence. This is deliberately a bounded parser, not a complete SARIF implementation or a general benchmark ingestion framework.

Multiple artifacts supplying the same metric are rejected even if values agree, avoiding silent precedence rules. Duplicate filenames and duplicate JSON keys are rejected. Path-like filenames are rejected; no uploaded content is written to an executable path.

## Limits

- At most eight artifacts in a bundle.
- At most 180,000 characters per file at the API schema; the browser uses a conservative 180,000-byte file limit.
- At most 400,000 UTF-8 bytes of combined artifact content.
- Request body middleware caps the complete incoming body at 1,000,000 bytes, including chunked requests without Content-Length.
- Coverage file count, SARIF runs and result counts are bounded.
- No source collection, archive extraction, PDF parsing or malware-scanning claim is made.

## Reproduction

The four files in `demo/reports/` are explicitly fictional fixtures. Create and approve the sample contract, switch to vendor access, upload them through the report importer and keep **Demonstration data** checked. Enter the same commit SHA, a fixture reference and an observation timestamp. After client inspection, run fixture verification. The UI shows parsed receipts and raw active evidence. Payment authorization remains prohibited.

`python scripts/http_smoke.py` exercises this through a real local HTTP server, then exports and replays the decision offline. It does not call Gemini or PayPal.

## Official format references

Consulted 2026-11-08:

- Coverage.py JSON reporting: https://coverage.readthedocs.io/en/latest/commands/cmd_json.html
- Coverage calculation semantics: https://coverage.readthedocs.io/en/7.12.0/faq.html
- k6 custom summary object: https://grafana.com/docs/k6/latest/results-output/end-of-test/custom-summary/
- GitHub SARIF support: https://docs.github.com/en/code-security/reference/code-scanning/sarif-files/sarif-support

These references informed field interpretation. They do not certify this parser, validate submitted files or prove sponsor usage. The 9.0 critical boundary is an explicit application policy, not a claim that every SARIF consumer applies the same threshold.
