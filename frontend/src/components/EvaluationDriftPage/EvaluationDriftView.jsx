// frontend/src/components/EvaluationDriftPage/EvaluationDriftView.jsx
import { useEffect, useState } from "react";
import { fetchEvaluationDrift } from "../../api/EvaluationDriftPage/api.js";

export default function EvaluationDriftView() {
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [items, setItems] = useState([]);

  useEffect(() => {
    async function run() {
      try {
        setLoading(true);
        setErrorMsg("");
        const data = await fetchEvaluationDrift();

        // Orchestrator returns either:
        // - Array (legacy/alt)
        // - { series, entries: [...] }
        const entries = Array.isArray(data)
          ? data
          : Array.isArray(data?.entries)
          ? data.entries
          : [];

        setItems(entries);
      } catch (e) {
        setErrorMsg(e?.message || "Failed to load drift data");
      } finally {
        setLoading(false);
      }
    }
    run();
  }, []);

  if (loading)
    return <div className="text-sm text-xtractyl-outline/70">Loading…</div>;

  if (errorMsg)
    return <div className="text-sm text-xtractyl-orange">{errorMsg}</div>;

  if (!items.length)
    return (
      <div className="text-sm text-xtractyl-outline/70">
        No drift data available yet.
      </div>
    );

  // sort: model → schema_hash → run_at_raw
  const sorted = [...items].sort((a, b) => {
    const m = String(a.model || "").localeCompare(String(b.model || ""));
    if (m !== 0) return m;

    const s = String(a.schema_hash || "").localeCompare(
      String(b.schema_hash || "")
    );
    if (s !== 0) return s;

    const ta = String(a.run_at_raw || "");
    const tb = String(b.run_at_raw || "");
    return ta.localeCompare(tb);
  });

  const cols = [
    "model",
    "schema_hash",
    "run_time",
    "precision",
    "recall",
    "f1",
    "n_files",
    "tp",
    "fp",
    "fn",
    "tn",
    "fp_fn",
    "timeout",
  ];

  return (
    <div className="overflow-x-auto border border-xtractyl-outline/20 rounded-lg bg-xtractyl-white shadow-sm">
      <table className="border-collapse text-sm whitespace-nowrap min-w-max w-full">
        <thead className="sticky top-0 bg-xtractyl-offwhite z-10">
          <tr>
            {cols.map((col) => (
              <th
                key={col}
                className="px-3 py-2 text-left border-b border-xtractyl-outline/20"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {sorted.map((it, idx) => {
            const micro = it.metrics?.micro || {};

            const tp = typeof micro.tp === "number" ? micro.tp : 0;
            const fp = typeof micro.fp === "number" ? micro.fp : 0;
            const fn = typeof micro.fn === "number" ? micro.fn : 0;
            const tn = typeof micro.tn === "number" ? micro.tn : 0;

            const fpFn = typeof micro.fp_fn === "number" ? micro.fp_fn : "—";
            const timeout = typeof micro.timeout === "number" ? micro.timeout : "—";

            const row = {
              model: it.model || "",
              schema_hash: it.schema_hash || "",
              run_time: it.run_at_raw ? new Date(it.run_at_raw).toLocaleString() : "",
              precision:
                typeof micro.precision === "number" ? micro.precision.toFixed(3) : "",
              recall: typeof micro.recall === "number" ? micro.recall.toFixed(3) : "",
              f1: typeof micro.f1 === "number" ? micro.f1.toFixed(3) : "",
              n_files: it.metrics?.filenames_count ?? "",
              tp,
              fp,
              fn,
              tn,
              fp_fn: fpFn,
              timeout,
            };

            return (
              <tr
                key={idx}
                className="border-b bg-xtractyl-white border-xtractyl-outline/10"
              >
                {cols.map((col) => (
                  <td key={col} className="px-3 py-2 align-top">
                    {row[col]}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}