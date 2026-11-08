"use client";

type Clause = {
  id: string;
  metric: string;
  operator: "gte" | "lte";
  threshold: string;
  deduction: string;
  text: string;
};
type Draft = {
  title: string;
  source_text: string;
  amount: string;
  currency: string;
  commit_sha: string;
  clauses: Clause[];
};
export default function ContractEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  let draft: Draft;
  try {
    draft = JSON.parse(value) as Draft;
    if (!Array.isArray(draft.clauses)) throw Error("Missing clauses");
  } catch {
    return (
      <p role="alert">
        Correct the JSON in the advanced editor to restore the form.
      </p>
    );
  }
  const update = (next: Draft) => onChange(JSON.stringify(next, null, 2));
  const field = (key: keyof Omit<Draft, "clauses">, text: string) =>
    update({ ...draft, [key]: text });
  const clause = (index: number, key: keyof Clause, text: string) =>
    update({
      ...draft,
      clauses: draft.clauses.map((c, i) =>
        i === index ? { ...c, [key]: text } : c,
      ),
    });
  return (
    <div className="contract-form">
      <label>
        Milestone title
        <input
          value={draft.title}
          onChange={(e) => field("title", e.target.value)}
        />
      </label>
      <div className="form-row">
        <label>
          Milestone amount (USD)
          <input
            type="number"
            min="0.01"
            step="0.01"
            value={draft.amount}
            onChange={(e) => field("amount", e.target.value)}
          />
        </label>
        <label>
          Currency
          <input value="USD" readOnly aria-label="Currency" />
        </label>
      </div>
      <label>
        Delivery commit SHA
        <input
          value={draft.commit_sha}
          maxLength={40}
          onChange={(e) => field("commit_sha", e.target.value)}
          spellCheck={false}
        />
      </label>
      <label>
        Original agreed terms
        <textarea
          rows={4}
          value={draft.source_text}
          onChange={(e) => field("source_text", e.target.value)}
        />
      </label>
      <p className="muted">
        Approve only terms agreed by both parties. Automatic report imports
        interpret coverage as statement coverage, not combined branch coverage.
      </p>
      {draft.clauses.map((c, i) => (
        <fieldset key={i} className="clause-editor">
          <legend>Clause {i + 1}</legend>
          <div className="form-row">
            <label>
              Clause ID
              <input
                value={c.id}
                onChange={(e) => clause(i, "id", e.target.value)}
              />
            </label>
            <label>
              Measurement
              <select
                value={c.metric}
                onChange={(e) => clause(i, "metric", e.target.value)}
              >
                <option value="coverage">Statement coverage (%)</option>
                <option value="p95_ms">P95 latency (ms)</option>
                <option value="critical_count">Critical finding count</option>
                <option value="documentation">Document presence (0 / 1)</option>
              </select>
            </label>
          </div>
          <label>
            Acceptance criterion
            <input
              value={c.text}
              onChange={(e) => clause(i, "text", e.target.value)}
            />
          </label>
          <div className="form-row three">
            <label>
              Comparison
              <select
                value={c.operator}
                onChange={(e) => clause(i, "operator", e.target.value)}
              >
                <option value="gte">At least</option>
                <option value="lte">At most</option>
              </select>
            </label>
            <label>
              Threshold
              <input
                type="number"
                min="0"
                step="any"
                value={c.threshold}
                onChange={(e) => clause(i, "threshold", e.target.value)}
              />
            </label>
            <label>
              Deduction (USD)
              <input
                type="number"
                min="0"
                step="0.01"
                value={c.deduction}
                onChange={(e) => clause(i, "deduction", e.target.value)}
              />
            </label>
          </div>
          <button
            disabled={draft.clauses.length <= 1}
            onClick={() =>
              update({
                ...draft,
                clauses: draft.clauses.filter((_, n) => n !== i),
              })
            }
          >
            Remove clause
          </button>
        </fieldset>
      ))}
      <button
        disabled={draft.clauses.length >= 20}
        onClick={() =>
          update({
            ...draft,
            clauses: [
              ...draft.clauses,
              {
                id: `SLA-${draft.clauses.length + 1}`,
                metric: "coverage",
                operator: "gte",
                threshold: "85",
                deduction: "0.00",
                text: "Statement coverage must meet the agreed threshold",
              },
            ],
          })
        }
      >
        Add clause
      </button>
    </div>
  );
}
