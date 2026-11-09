"use client";
import { useState } from "react";

type Finding = { clause_id: string; verdict: string; explanation: string; evidence_quote: string };
export type ReviewRecord = {
  at?: string;
  assessment?: { concern: string; findings: Finding[] };
  receipt: { mode: string; model: string; stages?: {
    role: string; input_hash: string; response_id?: string | null;
    output: { concern: string; findings: Finding[] };
  }[] };
};

export default function ReviewInspector({ review, source }: { review: ReviewRecord | null; source: string }) {
  const [filter, setFilter] = useState("all");
  if (!review) return <p className="empty">Run a review to inspect its stored reasoning and citations.</p>;
  const stages = review.receipt.stages || [];
  const clauses = Array.from(new Set(stages.flatMap(s => s.output.findings.map(f => f.clause_id))));
  const differences = clauses.filter(id => {
    const verdicts = stages.map(s => s.output.findings.find(f => f.clause_id === id)?.verdict || "missing");
    return new Set(verdicts).size > 1;
  });
  const visible = filter === "differences" ? differences : filter === "all" ? clauses : clauses.filter(id => `clause:${id}` === filter);
  return <section className="review-inspector">
    <div className="panel-title"><div><h2>Inside the review</h2><p>Stored outputs from sequential reviewers using the same model. The second stage receives the first stage’s findings.</p></div><span className="pill">{review.receipt.mode}</span></div>
    <p>Model: <b>{review.receipt.model}</b>{review.at && <> · Recorded {new Date(review.at).toLocaleString()}</>}</p>
    {review.assessment?.concern && <div className="notice error"><b>Final review concern: </b>{review.assessment.concern}</div>}
    {!stages.length ? <p className="notice">No provider stage receipts are present. Fixture output is simulated and cannot authorize a payment.</p> : <>
      <label>Inspect clauses<select value={filter} onChange={e => setFilter(e.target.value)}><option value="all">All clauses ({clauses.length})</option><option value="differences">Different or missing verdicts ({differences.length})</option>{clauses.map(id => <option key={id} value={`clause:${id}`}>{id}</option>)}</select></label>
      <div className="review-columns">{stages.map((stage, index) => <article className="review-stage" key={index}>
        <span className="eyebrow">STAGE {index + 1}</span><h3>{stage.role}</h3>
        {stage.output.concern && <p className="warn-text">Concern: {stage.output.concern}</p>}
        {visible.length === 0 && <p>No clauses match this filter. Matching verdicts alone do not prove correctness.</p>}
        {visible.map(id => {
          const finding = stage.output.findings.find(f => f.clause_id === id);
          return <div className="review-finding" key={id}><div className="panel-title"><b>{id}</b><span className={"pill " + (finding?.verdict === "pass" ? "good" : "warn")}>{finding?.verdict || "missing"}</span></div>
            {finding ? <><p>{finding.explanation}</p><details><summary>Show cited evidence</summary><blockquote>{finding.evidence_quote || "No quotation supplied"}</blockquote><small>{finding.evidence_quote && source.includes(finding.evidence_quote) ? "Exact text occurs in the submitted evidence. This does not establish source authenticity." : "Citation is empty or does not occur exactly in the submitted evidence."}</small></details></> : <p>No finding for this clause in this stage.</p>}
          </div>;
        })}
        <details><summary>Provider receipt details</summary><p className="hash">Input digest: {stage.input_hash}</p><p className="hash">Response ID: {stage.response_id || "Not supplied by provider"}</p></details>
      </article>)}</div>
      <p className="muted">This comparison is read-only. The server’s final assessment, citation checks and approved contract rules govern settlement eligibility.</p>
    </>}
  </section>;
}
