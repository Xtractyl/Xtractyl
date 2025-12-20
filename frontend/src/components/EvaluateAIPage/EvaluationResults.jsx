// src/components/EvaluateAIPage/EvaluationResults.jsx
import React from "react";

export default function EvaluationResults({ loading, errorMsg, result }) {
  if (loading) return <div className="mt-6">Running evaluation…</div>;
  if (errorMsg) return <div className="mt-6 text-red-600">{errorMsg}</div>;
  if (!result) return null;

  const payload = result.logs || result;
  const metrics = payload.metrics || {};
  const micro = metrics.micro || {};
  const perLabel = metrics.per_label || {};
  const taskMetrics = metrics.task_metrics || [];

  function Metric({ label, value }) {
    return (
      <div className="p-3 bg-[#f4f1e6] rounded border border-[#d3ccb8]">
        <div className="text-xs text-[#555]">{label}</div>
        <div className="text-lg font-semibold text-[#23211c]">
          {typeof value === "number" ? value.toFixed(3) : "—"}
        </div>
      </div>
    );
  }

  return (
    <div className="mt-8 space-y-6">
      {/* ---------- Project Info ---------- */}
      <div>
        <h2 className="text-xl font-semibold text-[#444038] border-b border-[#cfcab5] pb-1">
          Project Information
        </h2>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="p-3 bg-[#f4f1e6] rounded border border-[#d3ccb8]">
            <div className="font-semibold text-[#23211c]">Groundtruth Project</div>
            <div className="mt-1 text-[#444038]">
              Name: <b>{payload.groundtruth_project}</b>
              <br />
              ID: <span>{payload.groundtruth_project_id}</span>
            </div>
          </div>

          <div className="p-3 bg-[#f4f1e6] rounded border border-[#d3ccb8]">
            <div className="font-semibold text-[#23211c]">Comparison Project</div>
            <div className="mt-1 text-[#444038]">
              Name: <b>{payload.comparison_project}</b>
              <br />
              ID: <span>{payload.comparison_project_id}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ---------- Overall Metrics ---------- */}
      <div>
        <h2 className="text-xl font-semibold text-[#444038] border-b border-[#cfcab5] pb-1">
          Overall Metrics (Micro)
        </h2>

        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <Metric label="Precision" value={micro.precision} />
          <Metric label="Recall" value={micro.recall} />
          <Metric label="F1" value={micro.f1} />
          <Metric label="Accuracy" value={micro.accuracy} />
        </div>

        <div className="mt-3 text-xs text-[#555]">
          TP: {micro.tp} · FP: {micro.fp} · FN: {micro.fn} · TN: {micro.tn}
        </div>
      </div>

      {/* ---------- Per-Label Confusion ---------- */}
      <div>
        <h2 className="text-xl font-semibold text-[#444038] border-b border-[#cfcab5] pb-1">
          Per-Label Confusion
        </h2>

        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full border border-[#d3ccb8] text-sm">
            <thead className="bg-[#ebe7d8]">
              <tr>
                <th className="px-2 py-1 border">Label</th>
                <th className="px-2 py-1 border">TP</th>
                <th className="px-2 py-1 border">FP</th>
                <th className="px-2 py-1 border">FN</th>
                <th className="px-2 py-1 border">TN</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(perLabel).map(([label, m]) => (
                <tr key={label} className="odd:bg-[#f9f7ef]">
                  <td className="px-2 py-1 border font-medium">{label}</td>
                  <td className="px-2 py-1 border">{m.tp}</td>
                  <td className="px-2 py-1 border">{m.fp}</td>
                  <td className="px-2 py-1 border">{m.fn}</td>
                  <td className="px-2 py-1 border">{m.tn}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ---------- Per-Task Details ---------- */}
      <div>
        <h2 className="text-xl font-semibold text-[#444038] border-b border-[#cfcab5] pb-1">
          Per-Task Details
        </h2>

        <div className="mt-4 space-y-4">
          {taskMetrics.map((t) => (
            <div
              key={t.filename}
              className="p-3 bg-[#f9f7ef] rounded border border-[#d3ccb8]"
            >
              <div className="font-semibold text-sm text-[#23211c] mb-2">
                {t.filename}
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full border text-xs">
                  <thead className="bg-[#ebe7d8]">
                    <tr>
                      <th className="px-2 py-1 border">Label</th>
                      <th className="px-2 py-1 border">GT</th>
                      <th className="px-2 py-1 border">Pred</th>
                      <th className="px-2 py-1 border">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(t.per_label || {}).map(([lab, v]) => (
                      <tr key={lab} className="odd:bg-[#f4f1e6]">
                        <td className="px-2 py-1 border font-medium">{lab}</td>
                        <td className="px-2 py-1 border">{v.gt || "—"}</td>
                        <td className="px-2 py-1 border">{v.pred || "—"}</td>
                        <td className="px-2 py-1 border">{v.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}