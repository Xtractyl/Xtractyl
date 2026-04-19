// /src/components/EvaluationDriftPage/EvaluationDriftView.jsx
import { useEffect, useState } from "react";
import { fetchEvaluationDrift } from "../../api/EvaluationDriftPage/api.js";

import PlotEvaluationOverTimeGeneral from "./PlotEvaluationOverTimeGeneral.jsx"
import PlotEvaluationOverTimePerLabel from "./PlotEvaluationOverTimePerLabel.jsx"

export default function EvaluationDriftView() {
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [sets, setSets] = useState([]);
  const [selectedSeries, setSelectedSeries] = useState("");
  const [openPopover, setOpenPopover] = useState(null);

  useEffect(() => {
    async function run() {
      try {
        setLoading(true);
        setErrorMsg("");
        const data = await fetchEvaluationDrift();
        setSets(Array.isArray(data?.sets) ? data.sets : []);
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

  if (!sets.length || sets.every((s) => !s.entries?.length))
    return (
      <div className="text-sm text-xtractyl-outline/70">
        No drift data available yet.
      </div>
    );

      const seriesOptions = sets.map((s) => s.series);
  const visibleSets = selectedSeries
    ? sets.filter((s) => s.series === selectedSeries)
    : sets;

  const cols = [
    "#",
    "model",
    "system_prompt",
    "questions",
    "labels",
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
    <div className="space-y-16">
        <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-xtractyl-outline">
          GT Set:
        </label>
        <select
          value={selectedSeries}
          onChange={(e) => setSelectedSeries(e.target.value)}
          className="text-sm border border-xtractyl-outline/30 rounded px-2 py-1 bg-xtractyl-white"
        >
          <option value="">All</option>
          {seriesOptions.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {visibleSets.map((set) => {
        const seen = new Set();
        const deduped = (set.entries || []).filter((e) => {
          if (seen.has(e.run_at_raw)) return false;
          seen.add(e.run_at_raw);
          return true;
        });
        const numbered = deduped.map((e, i) => ({ ...e, number: i + 1 }));
        const sorted = [...numbered].sort((a, b) => {
          const m = String(a.model || "").localeCompare(String(b.model || ""));
          if (m !== 0) return m;
          return String(a.run_at_raw || "").localeCompare(
            String(b.run_at_raw || "")
          );
        });

        return (
          <div key={set.series}>
            <h3 className="text-sm font-semibold mb-2 text-xtractyl-outline">
              {set.series}
            </h3>
            <h4 className="text-sm font-medium text-xtractyl-outline mt-4 mb-1">
            Recall and Precision over Time
          </h4>
            <div className="overflow-x-auto">
              <PlotEvaluationOverTimeGeneral entries={numbered} />
            </div>
          <h4 className="text-sm font-medium text-xtractyl-outline mt-4 mb-1">
            Recall and Precision per Label over Time
          </h4>
          <div className="overflow-x-auto">
              <PlotEvaluationOverTimePerLabel entries={numbered} />
            </div>
            <h4 className="text-sm font-medium text-xtractyl-outline mt-4 mb-1">
            Raw Data
          </h4>
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
                    const fpFn =
                      typeof micro.fp_fn === "number" ? micro.fp_fn : "—";
                    const timeout =
                      typeof micro.timeout === "number" ? micro.timeout : "—";
                    const systemPrompt = it.system_prompt || "";
                    const questions = Array.isArray(it.questions)
                      ? it.questions.join("\n\n")
                      : "";
                    const labels = Array.isArray(it.labels)
                      ? it.labels.join("\n\n")
                      : "";

                    const row = {
                      "#": it.number,
                      model: it.model || "",
                      system_prompt:
                        systemPrompt.length > 10 ? (
                          <span
                            className="cursor-pointer text-xtractyl-green underline"
                            onClick={() => setOpenPopover({ key: `${idx}-prompt`, text: systemPrompt })}
                          >
                            {systemPrompt.slice(0, 10)}…
                          </span>
                        ) : (
                          systemPrompt
                        ),
                      questions:
                        questions.length > 10 ? (
                          <span
                            className="cursor-pointer text-xtractyl-green underline"
                            onClick={() => setOpenPopover({ key: `${idx}-prompt`, text: questions })}
                          >
                            {questions.slice(0, 10)}…
                          </span>
                        ) : (
                          questions
                        ),
                      labels:
                        labels.length > 10 ? (
                          <span
                            className="cursor-pointer text-xtractyl-green underline"
                            onClick={() => setOpenPopover({ key: `${idx}-prompt`, text: labels })}
                          >
                            {labels.slice(0, 10)}…
                          </span>
                        ) : (
                          labels
                        ),
                      run_time: it.run_at_raw
                        ? new Date(it.run_at_raw).toLocaleString()
                        : "",
                      precision:
                        typeof micro.precision === "number"
                          ? micro.precision.toFixed(3)
                          : "",
                      recall:
                        typeof micro.recall === "number"
                          ? micro.recall.toFixed(3)
                          : "",
                      f1:
                        typeof micro.f1 === "number"
                          ? micro.f1.toFixed(3)
                          : "",
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
            <h4 className="text-sm font-medium text-xtractyl-outline mt-16 mb-1">
            Recall and Precision for Regression Monitoring (same System Prompt, same Questions, [same Labels])
          </h4>
            <h5 className="text-xs font-normal text-xtractyl-outline/70 mt-4 mb-1">
            For exact System Prompt, Questions and Labels see Raw Data
          </h5>
           <div className="overflow-x-auto">
              <PlotEvaluationOverTimeGeneral entries={numbered} />
            </div>
          </div>
        );
      })}
            {openPopover && (
        <div
          className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center"
          onClick={() => setOpenPopover(null)}
        >
          <div
            className="bg-xtractyl-white rounded-lg shadow-lg p-6 max-w-lg w-full mx-4 max-h-96 overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <pre className="text-xs whitespace-pre-wrap break-words">
              {openPopover.text}
            </pre>
            <button
              className="mt-4 text-sm text-xtractyl-outline hover:text-xtractyl-darktext"
              onClick={() => setOpenPopover(null)}
            >
              Close+            </button>
          </div>
        </div>
      )}
    </div>
  );
}