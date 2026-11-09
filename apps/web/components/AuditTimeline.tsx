"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

type AuditEvent = { at: string; actor: string; event: string; version: number; record_hash: string; state_before?: string | null; state_after?: string; changed_fields?: string[] };
type Passport = { payload: { record: { id: string; version: number }; audit: AuditEvent[] } };
export default function AuditTimeline({ id, version, access, api }: { id: string; version: number; access: string; api: (path: string) => Promise<Passport> }) {
  const [actor, setActor] = useState("all"), [search, setSearch] = useState("");
  const result = useQuery({ queryKey: ["audit", id, version, access], queryFn: () => api(`/milestones/${id}/passport`), retry: false });
  const events = result.data?.payload.audit || [];
  const filtered = events.filter(e => (actor === "all" || e.actor === actor) && `${e.event} ${e.state_before || ""} ${e.state_after || ""} ${(e.changed_fields || []).join(" ")}`.toLowerCase().includes(search.toLowerCase())).slice().reverse();
  function exportEvents() {
    const blob = new Blob([JSON.stringify({ milestone_id: id, retrieved_record_revision: result.data?.payload.record.version, filters: { actor, search }, events: filtered, assurance: "Application event log; roles are shared deployment identities, not individual users. No immutable-ledger claim." }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob), a = document.createElement("a");
    a.href = url; a.download = `covenantx-${id}-audit.json`; a.click(); URL.revokeObjectURL(url);
  }
  return <section className="panel">
    <div className="panel-title"><div><h2>Milestone activity</h2><p>Inspect the event history, role and revision behind each recorded change.</p></div><button disabled={!result.data || result.isFetching} onClick={exportEvents}>Export filtered events</button></div>
    <div className="form-row"><label>Role<select value={actor} onChange={e => setActor(e.target.value)}><option value="all">All roles</option>{Array.from(new Set(events.map(e => e.actor))).map(a => <option key={a} value={a}>{a}</option>)}</select></label><label>Search event, state or field<input value={search} onChange={e => setSearch(e.target.value)} placeholder="For example: approved or evidence" /></label></div>
    {result.isPending && <p role="status">Loading recorded events…</p>}
    {result.error && <div role="alert"><p className="error">Could not load activity. {String(result.error)}</p><button onClick={() => result.refetch()}>Retry</button></div>}
    {result.data && <p>{filtered.length} of {events.length} events · newest first · retrieved record revision {result.data.payload.record.version}</p>}
    {result.data && !filtered.length && <p>No events match these filters.</p>}
    <ol className="audit-timeline">{filtered.map(e => <li key={e.version}><div className="panel-title"><b>{e.event.replaceAll(".", " / ")}</b><span className="pill">Revision {e.version}</span></div><p><b>{e.actor}</b> · <time dateTime={e.at}>{new Date(e.at).toLocaleString()}</time></p>{e.state_after && <p>{e.state_before || "New record"} → {e.state_after}</p>}<details><summary>Change metadata</summary>{e.changed_fields ? <p>Fields changed: {e.changed_fields.join(", ") || "None"}</p> : <p>This older event predates field-change summaries.</p>}<p className="hash">Record SHA-256: {e.record_hash}</p></details></li>)}</ol>
    <p className="muted">Actors identify shared client/vendor roles or system activity, not individual people. Hashes identify record content; this is not an independently authenticated or immutable ledger. Field summaries record names only, not previous values.</p>
  </section>;
}
