"use client";
import { useEffect, useState } from "react";
import ReviewInspector, { type ReviewRecord } from "../components/ReviewInspector";
import AuditTimeline from "../components/AuditTimeline";
import ContractEditor from "../components/ContractEditor";
import ArtifactImporter from "../components/ArtifactImporter";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import { z } from "zod";
import {
  ShieldCheck,
  ArrowUpRight,
  GitBranch,
  FileCheck2,
  Scale,
  Receipt,
  FlaskConical,
  LockKeyhole,
  RefreshCw,
  Download,
  Plus,
  ChevronRight,
  CheckCircle2,
  Circle,
  ArrowRight,
} from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

type Row = {
  clause_id: string;
  metric: string;
  observed: string;
  threshold: string;
  verdict: string;
  deduction: string;
  finding?: { explanation: string; evidence_quote: string };
};
type RecordData = {
  id: string;
  title: string;
  state: string;
  version: number;
  contract: {
    amount: string;
    currency: string;
    commit_sha: string;
    clauses: { id: string; text: string }[];
  };
  evidence: unknown;
  evidence_hash?: string;
  evidence_attestation?: unknown;
  evidence_provenance?: {
    parser: string;
    source_authenticity: string;
    artifacts: {
      name: string;
      format: string;
      sha256: string;
      derived_metrics: Record<string, string>;
    }[];
  };
  proposal: null | {
    amount: string;
    base: string;
    eligible: boolean;
    holds: string[];
    rows: Row[];
  };
  verification: ReviewRecord | null;
  payment: null | {
    order_id?: string;
    capture_id?: string;
    approval_url?: string;
    provider_status?: string;
  };
  disputes: { note: string; resolved: boolean }[];
};
const tabs = [
  "Overview",
  "Contract & evidence",
  "Verification",
  "Settlement studio",
  "CovenantGraph",
  "Disputes",
  "PayPal operations",
  "Evidence passport",
  "Activity log",
];
const sha = "a".repeat(40);
const initialContract = {
  title: "Atlas / Delivery milestone 02",
  source_text:
    "Milestone fee USD 5000. Coverage >=85%, deduction USD 500. P95 <=200ms, deduction USD 300. Zero critical issues, deduction USD 1000. Documentation required, deduction USD 200.",
  amount: "5000.00",
  currency: "USD",
  commit_sha: sha,
  clauses: [
    {
      id: "SLA-01",
      metric: "coverage",
      operator: "gte",
      threshold: "85",
      deduction: "500.00",
      text: "At least 85% automated test coverage",
    },
    {
      id: "SLA-02",
      metric: "p95_ms",
      operator: "lte",
      threshold: "200",
      deduction: "300.00",
      text: "P95 API response time at most 200 ms",
    },
    {
      id: "SLA-03",
      metric: "critical_count",
      operator: "lte",
      threshold: "0",
      deduction: "1000.00",
      text: "No unresolved critical security findings",
    },
    {
      id: "SLA-04",
      metric: "documentation",
      operator: "gte",
      threshold: "1",
      deduction: "200.00",
      text: "Required delivery documentation present",
    },
  ],
};
function exampleEvidence() {
  return {
    commit_sha: sha,
    artifact_id: "fixture-ci-104",
    source_url: "fixture://demo/ci-report",
    observed_at: new Date().toISOString(),
    content:
      "DEMONSTRATION INPUT. coverage=78%; p95_ms=180; critical_count=0; documentation=1. These measurements are fictional demo data.",
    metrics: {
      coverage: "78",
      p95_ms: "180",
      critical_count: "0",
      documentation: "1",
    },
    demonstration: true,
  };
}
function App() {
  const [token, setToken] = useState(""),
    [entry, setEntry] = useState(""),
    [tab, setTab] = useState(tabs[0]),
    [selected, setSelected] = useState(""),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [contract, setContract] = useState(
      JSON.stringify(initialContract, null, 2),
    ),
    [evidence, setEvidence] = useState(() =>
      JSON.stringify(exampleEvidence(), null, 2),
    ),
    [note, setNote] = useState(""),
    [coverage, setCoverage] = useState(90),
    [scenario, setScenario] = useState<{ amount: string } | null>(null),
    [graph, setGraph] = useState<{
      nodes: { id: string; label: string; hash?: string }[];
      edges: { source: string; target: string; relation: string }[];
    } | null>(null);
  const [recoveryOrder, setRecoveryOrder] = useState(""),
    [recoveryNote, setRecoveryNote] = useState(""),
    [replay, setReplay] = useState<{
      passed: boolean;
      checks: { check: string; passed: boolean; detail: string }[];
      limitations: string;
    } | null>(null);
  const reduced = useReducedMotion();
  async function api(path: string, body?: unknown) {
    const r = await fetch("/api" + path, {
      method: body === undefined ? "GET" : "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const value = await r.json();
    if (!r.ok)
      throw Error(
        typeof value.detail === "string"
          ? value.detail
          : JSON.stringify(value.detail),
      );
    return value;
  }
  const me = useQuery({
    queryKey: ["me", token],
    queryFn: () => api("/me"),
    enabled: !!token,
    retry: false,
  });
  const list = useQuery<RecordData[]>({
    queryKey: ["milestones", token],
    queryFn: () => api("/milestones"),
    enabled: !!token,
    retry: false,
    refetchInterval: 15000,
  });
  const health = useQuery({
    queryKey: ["health"],
    queryFn: () => fetch("/api/health").then((r) => r.json()),
    retry: false,
  });
  const d = list.data?.find((x) => x.id === selected) || list.data?.[0];
  const client = me.data?.role === "client";
  useEffect(() => {
    setScenario(null);
    setGraph(null);
    setReplay(null);
  }, [d?.id, d?.version, token]);
  async function run(action: () => Promise<unknown>, success = "Saved.") {
    setBusy(true);
    setMessage("");
    try {
      await action();
      await list.refetch();
      setMessage(success);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }
  function act(suffix: string, extra: object = {}) {
    return run(() =>
      api(`/milestones/${d!.id}/${suffix}`, { version: d!.version, ...extra }),
    );
  }
  function download(value: unknown, name: string) {
    const blob = new Blob([JSON.stringify(value, null, 2)], {
        type: "application/json",
      }),
      u = URL.createObjectURL(blob),
      a = document.createElement("a");
    a.href = u;
    a.download = name;
    a.click();
    URL.revokeObjectURL(u);
  }
  const locked =
    !!d &&
    [
      "CREATING",
      "CREATE_UNKNOWN",
      "ORDER_CREATED",
      "CAPTURING",
      "CAPTURE_UNKNOWN",
      "COMPLETED",
      "PROVIDER_REVIEW",
    ].includes(d.state);
  return (
    <div className="shell">
      <aside>
        <a className="brand" href="/">
          <span className="brand-icon">
            <ShieldCheck size={23} />
          </span>
          Covenant<span className="emerald">X</span>
        </a>
        <div className="small muted brand-sub">CONTRACT TO PAYPAL</div>
        <div className="workspace">
          <span className="avatar">CX</span>
          <div>
            Assurance workspace<small>Single client / vendor pair</small>
          </div>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav>
          {tabs.map((x, i) => (
            <button
              key={x}
              onClick={() => {
                setTab(x);
                setScenario(null);
                setGraph(null);
                setReplay(null);
              }}
              className={tab === x ? "active" : ""}
            >
              {
                [
                  <Scale key="a" />,
                  <FileCheck2 key="b" />,
                  <ShieldCheck key="c" />,
                  <Receipt key="d" />,
                  <GitBranch key="e" />,
                  <LockKeyhole key="f" />,
                  <ArrowUpRight key="g" />,
                  <FileCheck2 key="h" />,
                  <Receipt key="i" />,
                ][i]
              }
              {x}
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <span className="dot" />
          Sandbox only<small>No live money transfers</small>
          <button
            onClick={() => {
              setToken("");
              setEntry("");
              setSelected("");
            }}
            className="quiet"
          >
            Lock workspace
          </button>
        </div>
      </aside>
      <main>
        <header>
          <span className="muted">
            Workspace <ChevronRight size={13} /> {tab}
          </span>
          <span className="pill">{me.data?.role || "Locked"} access</span>
        </header>
        <div className="content">
          <div className="heading">
            <div>
              <div className="eyebrow">FINANCIAL ASSURANCE INTELLIGENCE</div>
              <h1>{tab}</h1>
              <p className="muted">
                Make the path from delivered work to justified payment visible.
              </p>
            </div>
            <button
              className="secondary"
              disabled={!token || busy}
              onClick={() => run(() => list.refetch(), "Updated from server.")}
            >
              <RefreshCw size={15} />
              Refresh
            </button>
          </div>
          <div className="notice">
            <FlaskConical size={18} />
            <span>
              <b>Development build.</b> Uploaded evidence requires human
              attestation. Fixture runs cannot authorize payments. Provider
              status is never simulated.
            </span>
          </div>
          {!token ? (
            <section className="panel login">
              <LockKeyhole size={28} />
              <h2>Open your workspace</h2>
              <p>
                Use the client or vendor token configured on your API server.
                Tokens stay in memory.
              </p>
              <label>
                Workspace access token
                <input
                  type="password"
                  value={entry}
                  onChange={(e) => setEntry(e.target.value)}
                  autoComplete="off"
                />
              </label>
              <button
                className="primary"
                onClick={() => {
                  setToken(entry);
                  setEntry("");
                }}
                disabled={entry.length < 32}
              >
                Unlock workspace <ArrowUpRight size={15} />
              </button>
            </section>
          ) : (
            <>
              {(me.error || list.error) && (
                <div role="alert" className="notice error">
                  {String(me.error || list.error)}
                </div>
              )}
              <div className="record-picker">
                <label>
                  Active milestone
                  <select
                    value={d?.id || ""}
                    onChange={(e) => {
                      setSelected(e.target.value);
                      setGraph(null);
                      setScenario(null);
                      setReplay(null);
                      setRecoveryOrder("");
                    }}
                  >
                    {!list.data?.length && <option>No milestones yet</option>}
                    {list.data?.map((x) => (
                      <option key={x.id} value={x.id}>
                        {x.title}
                      </option>
                    ))}
                  </select>
                </label>
                <span className="pill">{d?.state || "EMPTY WORKSPACE"}</span>
              </div>
              {tab === "Overview" && (
                <>
                  <div className="metrics">
                    <section className="panel">
                      <span className="muted">Milestone value</span>
                      <h2>${d?.contract.amount || "0.00"}</h2>
                      <small>USD · approved rules required</small>
                    </section>
                    <section className="panel">
                      <span className="muted">Proposed settlement</span>
                      <h2 className="emerald">${d?.proposal?.amount || "—"}</h2>
                      <small>
                        {d?.proposal
                          ? "Deterministic calculation"
                          : "Awaiting verified evidence"}
                      </small>
                    </section>
                    <section className="panel">
                      <span className="muted">Provider status</span>
                      <h2 className="status-text">
                        {d?.payment?.provider_status || "Not initiated"}
                      </h2>
                      <small>
                        {d?.payment?.capture_id
                          ? "Capture ID recorded"
                          : "No confirmed capture"}
                      </small>
                    </section>
                  </div>
                  <section className="panel">
                    <div className="panel-title">
                      <h2>From obligation to settlement</h2>
                      <span className="pill">Evidence first</span>
                    </div>
                    <p>Follow the live milestone state. Select a step to open its workspace.</p>
                    <div className="journey">
                      {[
                        { title: "Agree terms", detail: "Approve the milestone rules", target: "Contract & evidence", done: !!d && d.state !== "DRAFT" },
                        { title: "Inspect delivery", detail: "Vendor submits; client attests", target: "Contract & evidence", done: !!d?.evidence_attestation },
                        { title: "Review evidence", detail: "Run Gemini and inspect citations", target: "Verification", done: !!d?.verification },
                        { title: "Approve amount", detail: "Authorize the exact snapshot", target: "Settlement studio", done: ["APPROVED", "CREATING", "CREATE_UNKNOWN", "ORDER_CREATED", "CAPTURING", "CAPTURE_UNKNOWN", "COMPLETED", "PROVIDER_REVIEW"].includes(d?.state || "") },
                        { title: "Settle in Sandbox", detail: "Buyer approval, capture, reconcile", target: "PayPal operations", done: d?.state === "COMPLETED" },
                      ].map((step, i) => (
                        <button className="journey-step" key={step.title} onClick={() => setTab(step.target)} aria-label={`${step.done ? "Completed" : "Open"}: ${step.title}`}>
                          <span className={step.done ? "journey-icon done" : "journey-icon"}>
                            {step.done ? <CheckCircle2 size={20} /> : <Circle size={20} />}
                          </span>
                          <span className="journey-copy"><b>{String(i + 1).padStart(2, "0")} · {step.title}</b><small>{step.detail}</small></span>
                          <ArrowRight size={15} />
                        </button>
                      ))}
                    </div>
                  </section>
                  <section className="panel impact-panel">
                    <div className="panel-title">
                      <div><h2>How evidence reaches PayPal</h2><p>AI reviews evidence. Approved contract rules calculate the amount; the client authorizes the resulting snapshot.</p></div>
                      <span className="pill">AUDITABLE</span>
                    </div>
                    <div className="impact-flow">
                      <div><small>Contract amount</small><b>${d?.contract.amount || "—"}</b></div>
                      <span aria-hidden="true">−</span>
                      <div><small>Rule deductions</small><b>${d?.proposal ? (Number(d.proposal.base) - Number(d.proposal.amount)).toFixed(2) : "—"}</b></div>
                      <span aria-hidden="true">=</span>
                      <div className="impact-result"><small>Proposed PayPal amount</small><b>${d?.proposal?.amount || "—"}</b></div>
                    </div>
                    <div className="impact-foot">
                      <span>{d?.proposal?.rows.length ?? 0} clause findings</span>
                      <span>{d?.proposal?.holds.length ? `${d.proposal.holds.length} hold(s) block approval` : d?.proposal ? "No review holds" : "Run evidence review to calculate"}</span>
                      <button className="quiet" onClick={() => setTab("Settlement studio")}>Inspect calculation <ArrowUpRight size={14} /></button>
                    </div>
                  </section>
                  <div className="two">
                    <section className="panel">
                      <h2>Connection readiness</h2>
                      <p>
                        PayPal credentials:{" "}
                        <b>
                          {health.data?.paypal_configured
                            ? "Configured; execution unverified"
                            : "Not configured"}
                        </b>
                      </p>
                      <p>
                        Gemini credentials:{" "}
                        <b>
                          {health.data?.ai_configured
                            ? "Configured; execution unverified"
                            : "Not configured"}
                        </b>
                      </p>
                    </section>
                    <section className="panel">
                      <h2>Current evidence assurance</h2>
                      <p>
                        {d?.evidence_attestation
                          ? "Human-attested artifact. No independent CI authenticity claim."
                          : "No client attestation recorded."}
                      </p>
                      <p className="muted">
                        Hashes establish content identity, not source
                        authenticity.
                      </p>
                    </section>
                  </div>
                </>
              )}
              {tab === "Contract & evidence" && (
                <div className="two">
                  <section className="panel">
                    <h2>1 / Contract rules</h2>
                    <p>
                      Review the supplied example or replace it with your agreed
                      terms. USD only.
                    </p>
                    <ContractEditor value={contract} onChange={setContract} />
                    <details>
                      <summary>Advanced contract JSON</summary>
                      <label>
                        Contract JSON
                        <textarea
                          rows={12}
                          value={contract}
                          onChange={(e) => setContract(e.target.value)}
                        />
                      </label>
                    </details>
                    <div className="actions">
                      <button
                        className="primary"
                        disabled={!client || busy}
                        onClick={() =>
                          run(async () => {
                            const value = z
                              .object({ title: z.string(), amount: z.string() })
                              .passthrough()
                              .parse(JSON.parse(contract));
                            const created = await api("/milestones", value);
                            setSelected(created.id);
                          }, "Draft created. Review and freeze its financial rules.")
                        }
                      >
                        <Plus size={15} />
                        Create draft
                      </button>
                      <button
                        disabled={!client || !d || d.state !== "DRAFT" || busy}
                        onClick={() =>
                          run(
                            () =>
                              api(`/milestones/${d!.id}/contract`, {
                                version: d!.version,
                                contract: JSON.parse(contract),
                              }),
                            "Draft updated. Inspect the active contract before approving.",
                          )
                        }
                      >
                        Save edits to active draft
                      </button>
                      <button
                        disabled={!client || !d || d.state !== "DRAFT" || busy}
                        onClick={() => act("approve-contract")}
                      >
                        Approve active contract
                      </button>
                    </div>
                    {d && (
                      <details>
                        <summary>Inspect active contract</summary>
                        <pre>{JSON.stringify(d.contract, null, 2)}</pre>
                      </details>
                    )}
                  </section>
                  <section className="panel">
                    <h2>2 / Delivery evidence</h2>
                    <p>
                      Import report files to derive measurements, or use the
                      advanced manual evidence editor.
                    </p>
                    {d && (
                      <ArtifactImporter
                        key={d.id}
                        commit={d.contract.commit_sha}
                        disabled={
                          client || locked || busy || d.state === "DRAFT"
                        }
                        onImport={(body) =>
                          run(
                            () =>
                              api(
                                `/milestones/${d.id}/evidence/import?version=${d.version}`,
                                body,
                              ),
                            "Reports parsed and saved. Client source inspection is still required.",
                          )
                        }
                      />
                    )}
                    <details>
                      <summary>Advanced manual evidence / fixture</summary>
                      <label>
                        Evidence JSON
                        <textarea
                          rows={14}
                          value={evidence}
                          onChange={(e) => setEvidence(e.target.value)}
                        />
                      </label>
                      <button
                        disabled={client || !d || locked || busy}
                        onClick={() =>
                          run(() =>
                            api(
                              `/milestones/${d!.id}/evidence?version=${d!.version}`,
                              JSON.parse(evidence),
                            ),
                          )
                        }
                      >
                        Submit as vendor
                      </button>
                    </details>
                    {d?.evidence_provenance && (
                      <div className="provenance">
                        <h3>Parsed artifact receipts</h3>
                        <p>{d.evidence_provenance.source_authenticity}</p>
                        {d.evidence_provenance.artifacts.map((a) => (
                          <details key={a.name}>
                            <summary>{a.name}</summary>
                            <p>{a.format}</p>
                            <pre>
                              {JSON.stringify(a.derived_metrics, null, 2)}
                            </pre>
                            <small className="hash">SHA-256 {a.sha256}</small>
                          </details>
                        ))}
                      </div>
                    )}
                    {d?.evidence != null && (
                      <details open>
                        <summary>Inspect active submitted evidence</summary>
                        <pre>{JSON.stringify(d.evidence, null, 2)}</pre>
                      </details>
                    )}
                    <label>
                      Client inspection note
                      <textarea
                        rows={3}
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                        placeholder="Describe how you checked the source, commit and measurement values."
                      />
                    </label>
                    <button
                      disabled={
                        !client ||
                        !d?.evidence ||
                        locked ||
                        note.length < 5 ||
                        busy
                      }
                      onClick={() => act("attest", { note })}
                    >
                      Attest active evidence
                    </button>
                  </section>
                </div>
              )}
              {tab === "Verification" && (
                <section className="panel">
                  <div className="panel-title">
                    <div>
                      <h2>Grounded verification</h2>
                      <p>
                        Sequential technical and adversarial reviews. Exact
                        quotations and measurements are checked server-side.
                      </p>
                    </div>
                    <span className="pill">
                      {d?.verification?.receipt.mode || "NOT RUN"}
                    </span>
                  </div>
                  <div className="actions">
                    <button
                      className="primary"
                      disabled={
                        !client || !d?.evidence_attestation || locked || busy
                      }
                      onClick={() => act("verify", { mode: "gemini" })}
                    >
                      Run Gemini review
                    </button>
                    <button
                      disabled={
                        !client || !d?.evidence_attestation || locked || busy
                      }
                      onClick={() => act("verify", { mode: "fixture" })}
                    >
                      Run labeled fixture
                    </button>
                  </div>
                  {d?.proposal?.holds.map((x) => (
                    <p className="error" key={x}>
                      {x}
                    </p>
                  ))}
                  <EvidenceTable rows={d?.proposal?.rows || []} />
                  <ReviewInspector key={`${d?.id}-${d?.version}`} review={d?.verification || null} source={d?.evidence && typeof d.evidence === "object" && "content" in d.evidence ? String(d.evidence.content) : ""} />
                </section>
              )}
              {tab === "Settlement studio" && (
                <div className="two">
                  <section className="panel">
                    <h2>Explainable settlement</h2>
                    <p>
                      Only approved clause deductions affect the amount. The
                      browser never submits a payment amount.
                    </p>
                    <EvidenceTable rows={d?.proposal?.rows || []} />
                    <div className="total">
                      <span>Proposed payment</span>
                      <strong>${d?.proposal?.amount || "—"}</strong>
                    </div>
                    <button
                      className="primary"
                      disabled={!client || d?.state !== "PROPOSED" || busy}
                      onClick={() => act("approve-settlement")}
                    >
                      Approve settlement snapshot
                    </button>
                    <p className="muted">
                      Fixture runs, demonstration evidence, open disputes and
                      stale evidence are blocked by the server.
                    </p>
                  </section>
                  <section className="panel simulator">
                    <span className="pill">HYPOTHETICAL · NO WRITE</span>
                    <h2>What changes at 90%?</h2>
                    <p>
                      Explore how the approved coverage rule affects the
                      proposed payment.
                    </p>
                    <label>
                      Hypothetical coverage: {coverage}%
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={coverage}
                        onChange={(e) => {
                          setCoverage(Number(e.target.value));
                          setScenario(null);
                        }}
                      />
                    </label>
                    <button
                      disabled={!d?.verification || busy}
                      onClick={() =>
                        run(async () => {
                          const r = await api(`/milestones/${d!.id}/simulate`, {
                            coverage,
                          });
                          setScenario(r.scenario);
                        }, "Hypothetical calculation only. No settlement was changed.")
                      }
                    >
                      Compare scenario
                    </button>
                    {scenario && (
                      <motion.div
                        initial={reduced ? false : { opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="comparison"
                      >
                        <div>
                          <small>Current</small>
                          <h2>${d?.proposal?.amount}</h2>
                        </div>
                        <ChevronRight />
                        <div>
                          <small>Hypothetical</small>
                          <h2 className="emerald">${scenario.amount}</h2>
                        </div>
                      </motion.div>
                    )}
                  </section>
                </div>
              )}
              {tab === "CovenantGraph" && (
                <section className="panel">
                  <div className="panel-title">
                    <div>
                      <h2>Trace every finding</h2>
                      <p>
                        Inspect the contract → clause → artifact → finding
                        relationships.
                      </p>
                    </div>
                    <button
                      disabled={!d || busy}
                      onClick={() =>
                        run(
                          async () =>
                            setGraph(await api(`/milestones/${d!.id}/graph`)),
                          "Graph loaded from stored records.",
                        )
                      }
                    >
                      Load graph
                    </button>
                  </div>
                  {graph && (
                    <div className="graph">
                      {graph.edges.map((edge, i) => (
                        <div className="edge" key={i}>
                          <div>
                            <small>{edge.source}</small>
                            <b>
                              {
                                graph.nodes.find((n) => n.id === edge.source)
                                  ?.label
                              }
                            </b>
                          </div>
                          <span>
                            {edge.relation}
                            <ChevronRight />
                          </span>
                          <div>
                            <small>{edge.target}</small>
                            <b>
                              {
                                graph.nodes.find((n) => n.id === edge.target)
                                  ?.label
                              }
                            </b>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              )}
              {tab === "Disputes" && (
                <section className="panel">
                  <h2>Challenge the evidence or deduction</h2>
                  <p>
                    Open disputes invalidate settlement approval. The vendor
                    closes a challenge with a resolution note; the client must
                    approve the result again.
                  </p>
                  {d?.disputes.map((x, i) => (
                    <div className="dispute" key={i}>
                      <span className="pill">
                        {x.resolved ? "Resolved" : "Open"}
                      </span>
                      <p>{x.note}</p>
                    </div>
                  ))}
                  <label>
                    Challenge or resolution note
                    <textarea
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      rows={4}
                    />
                  </label>
                  <div className="actions">
                    <button
                      disabled={!d || locked || note.length < 5 || busy}
                      onClick={() => act("dispute", { note })}
                    >
                      Open challenge
                    </button>
                    <button
                      disabled={
                        client || !d || locked || note.length < 5 || busy
                      }
                      onClick={() => act("resolve", { note })}
                    >
                      Resolve as vendor
                    </button>
                  </div>
                </section>
              )}
              {tab === "PayPal operations" && (
                <section className="panel">
                  <div className="panel-title">
                    <h2>Sandbox transaction control</h2>
                    <span className="pill">PAYPAL ORDERS V2</span>
                  </div>
                  <p>
                    Order creation is not payment. Complete payer approval on
                    PayPal, then capture and reconcile.
                  </p>
                  <div className="actions">
                    <button
                      className="primary"
                      disabled={!client || d?.state !== "APPROVED" || busy}
                      onClick={() => act("order")}
                    >
                      Create sandbox order
                    </button>
                    {d?.payment?.approval_url && (
                      <a
                        className="button"
                        href={d.payment.approval_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Approve on PayPal <ArrowUpRight size={15} />
                      </a>
                    )}
                    <button
                      disabled={!client || d?.state !== "ORDER_CREATED" || busy}
                      onClick={() => act("capture")}
                    >
                      Capture approved order
                    </button>
                    <button
                      disabled={!client || !d?.payment || busy}
                      onClick={() => act("reconcile")}
                    >
                      Reconcile provider
                    </button>
                  </div>
                  <pre>
                    {JSON.stringify(
                      d?.payment || { status: "No payment attempt" },
                      null,
                      2,
                    )}
                  </pre>
                  <details>
                    <summary>Recover an interrupted payment</summary>
                    <p>
                      Wait at least two minutes. Enter an order ID found in your
                      sandbox merchant dashboard and record your inspection.
                      Recovery only retrieves provider state; it cannot create
                      or capture a payment.
                    </p>
                    <label>
                      Candidate PayPal order ID
                      <input
                        value={recoveryOrder}
                        onChange={(e) => setRecoveryOrder(e.target.value)}
                        placeholder={
                          d?.payment?.order_id ||
                          "Order ID from sandbox dashboard"
                        }
                      />
                    </label>
                    <label>
                      Recovery inspection note
                      <textarea
                        rows={3}
                        value={recoveryNote}
                        onChange={(e) => setRecoveryNote(e.target.value)}
                      />
                    </label>
                    <button
                      disabled={
                        !client ||
                        !d?.payment ||
                        recoveryOrder.length < 5 ||
                        recoveryNote.length < 5 ||
                        busy
                      }
                      onClick={() =>
                        act("recover", {
                          order_id: recoveryOrder,
                          note: recoveryNote,
                        })
                      }
                    >
                      Verify candidate order and recover
                    </button>
                  </details>
                </section>
              )}
              {tab === "Activity log" && (d ? <AuditTimeline key={d.id} id={d.id} version={d.version} access={token} api={api} /> : <section className="panel"><p>Create a milestone to start its activity history.</p></section>)}
              {tab === "Evidence passport" && (
                <section className="panel">
                  <FileCheck2 className="emerald" size={32} />
                  <h2>A portable decision record</h2>
                  <p>
                    Export the contract, evidence, model outputs, deductions,
                    approvals, payment identifiers and audit events with a
                    canonical SHA-256 digest.
                  </p>
                  <p className="muted">
                    This is an inspectable record, not a digital signature or a
                    guarantee of source authenticity.
                  </p>
                  <div className="actions">
                    <button
                      disabled={!d?.verification || busy}
                      onClick={() =>
                        run(
                          async () =>
                            setReplay(await api(`/milestones/${d!.id}/replay`)),
                          "Policy replay completed without external calls.",
                        )
                      }
                    >
                      Replay stored decision
                    </button>
                    <button
                      className="primary"
                      disabled={!d || busy}
                      onClick={() =>
                        run(
                          async () =>
                            download(
                              await api(`/milestones/${d!.id}/passport`),
                              `covenantx-${d!.id}-passport.json`,
                            ),
                          "Passport exported.",
                        )
                      }
                    >
                      <Download size={16} />
                      Export evidence passport
                    </button>
                  </div>
                  {replay && (
                    <div className="replay-results">
                      <span
                        className={"pill " + (replay.passed ? "good" : "warn")}
                      >
                        {replay.passed ? "CONSISTENT" : "CHECKS FAILED"}
                      </span>
                      {replay.checks.map((x) => (
                        <p key={x.check}>
                          <b>
                            {x.passed ? "PASS" : "FAIL"} · {x.check}
                          </b>
                          <br />
                          {x.detail}
                        </p>
                      ))}
                      <p>{replay.limitations}</p>
                    </div>
                  )}
                </section>
              )}
            </>
          )}
          {message && (
            <div className="feedback" role="status">
              {message}
            </div>
          )}
          {busy && (
            <div className="feedback" role="status">
              Request in progress…
            </div>
          )}
          <footer>
            <span>CovenantX / Financial assurance intelligence</span>
            <span>
              Development build · Polls every 15 seconds when unlocked
            </span>
          </footer>
        </div>
      </main>
    </div>
  );
}
function EvidenceTable({ rows }: { rows: Row[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Clause / metric</th>
            <th>Observed</th>
            <th>Threshold</th>
            <th>Finding</th>
            <th>Deduction</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.clause_id}>
              <td>
                <b>{r.clause_id}</b>
                <small>{r.metric}</small>
                {r.finding && (
                  <details>
                    <summary>Evidence</summary>
                    <p>{r.finding.explanation}</p>
                    <blockquote>{r.finding.evidence_quote}</blockquote>
                  </details>
                )}
              </td>
              <td>{r.observed ?? "Missing"}</td>
              <td>{r.threshold}</td>
              <td>
                <span
                  className={"pill " + (r.verdict === "pass" ? "good" : "warn")}
                >
                  {r.verdict}
                </span>
              </td>
              <td>${r.deduction}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {!rows.length && <p className="empty">No verification findings yet.</p>}
    </div>
  );
}
export default function Page() {
  const [queryClient] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  );
}
