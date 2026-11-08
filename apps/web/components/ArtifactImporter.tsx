"use client";
import { useState } from "react";

type Artifact = { name: string; format: string; content: string };
const formats = [
  {
    id: "coverage-py-json",
    label: "Coverage.py JSON",
    hint: "Statement coverage from file counts; inconsistent totals are rejected.",
    accept: ".json",
  },
  {
    id: "k6-summary-json",
    label: "k6 custom summary JSON",
    hint: "P95 from the uploaded HTTP duration trend; no sample-level recomputation.",
    accept: ".json",
  },
  {
    id: "sarif-2.1-json",
    label: "Security report (SARIF 2.1)",
    hint: "Successful invocation and declared security rules required.",
    accept: ".sarif,.json",
  },
  {
    id: "documentation-text",
    label: "Delivery documentation",
    hint: "Plain text or Markdown. Presence is parsed; completeness still needs review.",
    accept: ".txt,.md",
  },
];
export default function ArtifactImporter({
  commit,
  disabled,
  onImport,
}: {
  commit: string;
  disabled: boolean;
  onImport: (body: unknown) => Promise<void>;
}) {
  const [artifacts, setArtifacts] = useState<Record<string, Artifact>>({});
  const [sha, setSha] = useState(commit),
    [source, setSource] = useState(""),
    [run, setRun] = useState("");
  const [observed, setObserved] = useState(() => new Date().toISOString());
  const [demo, setDemo] = useState(true),
    [error, setError] = useState("");
  async function read(format: string, file?: File) {
    if (!file) return;
    setError("");
    try {
      if (file.size > 180000)
        throw Error("Each file must be at most 180,000 bytes.");
      const text = await file.text();
      setArtifacts((previous) => ({
        ...previous,
        [format]: { name: file.name, format, content: text },
      }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not read file");
    }
  }
  return (
    <section className="artifact-import">
      <h3>Import delivery reports</h3>
      <p>
        Measurements are derived on the server. Files are stored as evidence and
        never executed. Uploading a report does not authenticate its source.
      </p>
      {formats.map((f) => (
        <div className="upload-row" key={f.id}>
          <label>
            {f.label}
            <input
              type="file"
              accept={f.accept}
              disabled={disabled}
              onChange={(e) => read(f.id, e.target.files?.[0])}
            />
          </label>
          <small>{f.hint}</small>
          {artifacts[f.id] && (
            <div className="upload-selected">
              <span>{artifacts[f.id].name}</span>
              <button
                onClick={() =>
                  setArtifacts((previous) => {
                    const copy = { ...previous };
                    delete copy[f.id];
                    return copy;
                  })
                }
              >
                Remove
              </button>
            </div>
          )}
        </div>
      ))}
      <label>
        Commit associated with these reports
        <input
          value={sha}
          onChange={(e) => setSha(e.target.value)}
          maxLength={40}
        />
      </label>
      <label>
        CI run / artifact reference
        <input value={run} onChange={(e) => setRun(e.target.value)} />
      </label>
      <label>
        Source URL (recorded; not fetched)
        <input value={source} onChange={(e) => setSource(e.target.value)} />
      </label>
      <label>
        Report observation time (ISO 8601 with timezone)
        <input value={observed} onChange={(e) => setObserved(e.target.value)} />
      </label>
      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={demo}
          onChange={(e) => setDemo(e.target.checked)}
        />
        Demonstration data — payment authorization blocked
      </label>
      {!demo && (
        <p className="warn-text">
          Only clear this for genuine delivery evidence. Do not relabel the
          supplied fixtures as real results.
        </p>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <button
        className="primary"
        disabled={
          disabled ||
          !Object.keys(artifacts).length ||
          !run.trim() ||
          !source.trim() ||
          sha.length !== 40
        }
        onClick={() =>
          onImport({
            commit_sha: sha,
            artifact_id: run,
            source_url: source,
            observed_at: observed,
            demonstration: demo,
            artifacts: Object.values(artifacts),
          })
        }
      >
        Parse and submit reports
      </button>
    </section>
  );
}
