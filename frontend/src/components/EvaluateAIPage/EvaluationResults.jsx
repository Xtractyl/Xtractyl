// src/components/EvaluateAIPage/EvaluationResults.jsx
import React from "react";

export default function EvaluationResults({ loading, errorMsg, result }) {
  if (loading) return <div className="mt-6">Running evaluation…</div>;
  if (errorMsg) return <div className="mt-6 text-xtractyl-orange">{errorMsg}</div>;
  if (!result) return null;

  const payload = result.logs || result;
  const metrics = payload.metrics || {};
  const micro = metrics.micro || {};
  const perLabel = metrics.per_label || {};
  const taskMetrics = metrics.task_metrics || [];

  const cmpMeta =
    taskMetrics.find((t) => t?.meta && Object.keys(t.meta).length > 0)?.meta || {};

  function Metric({ label, value }) {
    return (
      <div className="p-3 bg-xtractyl-white rounded border border-xtractyl-outline/20">
        <div className="text-xs text-xtractyl-outline/80">{label}</div>
        <div className="text-lg font-semibold text-xtractyl-darktext">
          {typeof value === "number" ? value.toFixed(3) : "—"}
        </div>
      </div>
    );
  }

  return (
    <div className="mt-8 space-y-6">

      {/* ---------- Project Info ---------- */}
      <div>
        <h2 className="text-xl font-semibold text-xtractyl-outline border-b pb-1">
          Project Information
        </h2>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="p-3 bg-xtractyl-white rounded border">
            <div className="font-semibold">Groundtruth Project</div>
            <div className="mt-1">
              Name: <b>{payload.groundtruth_project}</b><br />
              ID: {payload.groundtruth_project_id}
            </div>
          </div>

          <div className="p-3 bg-xtractyl-white rounded border">
            <div className="font-semibold">Comparison Project</div>
            <div className="mt-1">
              Name: <b>{payload.comparison_project}</b><br />
              ID: {payload.comparison_project_id}<br />
              Model: {cmpMeta.model ?? "—"}
            </div>
          </div>
        </div>
      </div>

      {cmpMeta.system_prompt && (
        <div className="p-3 bg-xtractyl-white rounded border">
          <div className="font-semibold text-sm mb-1">System Prompt</div>
          <pre className="text-xs whitespace-pre-wrap">
            {cmpMeta.system_prompt}
          </pre>
        </div>
      )}

      {/* ---------- Overall Metrics ---------- */}
      <div>
        <h2 className="text-xl font-semibold border-b pb-1">
          Overall Metrics (Micro)
        </h2>

        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <Metric label="Precision" value={micro.precision} />
          <Metric label="Recall" value={micro.recall} />
          <Metric label="F1" value={micro.f1} />
          <Metric label="Accuracy" value={micro.accuracy} />
        </div>

        <div className="mt-2 text-xs">
          TP {micro.tp} · FP {micro.fp} · FN {micro.fn} · TN {micro.tn}
        </div>
      </div>

      {/* ---------- Per-Label Metrics ---------- */}
      <div>
        <h2 className="text-xl font-semibold border-b pb-1">
          Per-Label Metrics
        </h2>

        <div className="mt-4 space-y-4">
          {Object.entries(perLabel).map(([label, m]) => (
            <div key={label} className="p-3 bg-xtractyl-white rounded border">
              <div className="font-semibold text-sm mb-2">{label}</div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                <Metric label="Precision" value={m.precision} />
                <Metric label="Recall" value={m.recall} />
                <Metric label="F1" value={m.f1} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ---------- Per-Task Details ---------- */}
      <div>
        <h2 className="text-xl font-semibold border-b pb-1">
          Per-Task Details
        </h2>

        <div className="mt-4 space-y-4">
          {taskMetrics.map((t) => {
            const llmCalls =
              (t.meta?.performance?.events || [])
                .filter((e) => e?.name === "llm.call")
                .map((e, idx) => ({
                  idx,
                  ms: e.ms,
                  label: e.tags?.label,
                  status: e.tags?.status,
                }));

            return (
              <div key={t.filename} className="p-3 bg-xtractyl-white rounded border">
                <div className="font-semibold text-sm mb-2">
                  {t.filename}
                </div>

                <table className="min-w-full border text-xs mb-3">
                  <thead className="bg-xtractyl-white">
                    <tr>
                      <th className="border px-2 py-1">Label</th>
                      <th className="border px-2 py-1">GT</th>
                      <th className="border px-2 py-1">Pred</th>
                      <th className="border px-2 py-1">Raw</th>
                      <th className="border px-2 py-1">DOM</th>
                      <th className="border px-2 py-1">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(t.per_label || {}).map(([lab, v]) => (
                      <tr key={lab}>
                        <td className="border px-2 py-1">{lab}</td>
                        <td className="border px-2 py-1">{v.gt ?? "—"}</td>
                        <td className="border px-2 py-1">{v.pred ?? "—"}</td>
                        <td className="border px-2 py-1 whitespace-pre-wrap">
                          {t.meta?.raw_llm_answers?.[lab]?.answer ?? "—"}
                        </td>
                        <td className="border px-2 py-1 text-xtractyl-outline/70">
                          {t.meta?.dom_match_by_label?.[lab] === true
                            ? "✓"
                            : t.meta?.dom_match_by_label?.[lab] === false
                            ? "✗"
                            : "—"}
                        </td>
                        <td className="border px-2 py-1">{v.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {/* ---------- LLM Calls ---------- */}
                {llmCalls.length > 0 && (
                  <div className="p-3 bg-xtractyl-white rounded border">
                    <div className="text-sm font-semibold mb-2">
                      LLM call durations (ms)
                    </div>
                    <div className="space-y-1 text-xs">
                      {llmCalls.map((c) => (
                        <div key={c.idx} className="flex justify-between">
                          <div>
                            {c.label ?? "—"} {c.status ? `(${c.status})` : ""}
                          </div>
                          <div className="font-mono">
                            {typeof c.ms === "number" ? c.ms.toFixed(1) : "—"}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}

                      {/* ---------- Performance Metrics (Aggregated) ---------- */}
            {metrics.performance && (
              <div>
                <h2 className="text-xl font-semibold text-xtractyl-outline border-b border-xtractyl-outline/20 pb-1">
                  Performance (Backend)
                </h2>

                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <Metric label="Average Time Per Task [DOM extraction + LLM + DOM matching] (ms)" value={metrics.performance.task_ms_total_avg} />
                  <Metric label="Average DOM Extraction Time Per Task (ms)" value={metrics.performance.task_ms_dom_extract_avg} />
                  <Metric label="Average DOM Matching Time Per Task (ms)" value={metrics.performance.task_ms_dom_match_avg} />
                  <Metric label="Average LLM Time Per Task (ms)" value={metrics.performance.task_ms_llm_total_avg} />
                </div>

                <div className="mt-3 text-xs text-xtractyl-outline/80">
                  Number of Tasks: {metrics.performance.n_tasks_with_perf} ·{" "}
                  p95 for Time Per Task [DOM extraction + LLM + DOM matching]: {metrics.performance.task_ms_total_p95.toFixed(1)} ms ·{" "}
                  p95 for LLM Time Per Task: {metrics.performance.task_ms_llm_total_p95.toFixed(1)} ms
                </div>
              </div>
            )}
        </div>
      </div>
    </div>
  );
}