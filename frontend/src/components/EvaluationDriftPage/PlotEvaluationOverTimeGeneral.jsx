// src/components/EvaluationDriftPage/PlotEvaluationOverTimeGeneral.jsx
import Plot from "react-plotly.js";

export default function PlotEvaluationOverTime({ entries }) {
  if (!entries?.length) return null;

  const sorted = [...entries].sort((a, b) =>
    String(a.run_at_raw || "").localeCompare(String(b.run_at_raw || ""))
  );

  const x = sorted.map((e) => new Date(e.run_at_raw));
  const precision = sorted.map((e) => e.metrics?.micro?.precision ?? null);
  const recall = sorted.map((e) => e.metrics?.micro?.recall ?? null);
  const numbers = sorted.map((_, i) => String(i + 1));

  const tracePrecision = {
    x,
    y: precision,
    mode: "lines+markers+text",
    name: "Precision",
    text: numbers,
    textposition: "top center",
    marker: { size: 6 },
    line: { color: "#f97316" },
  };

  const traceRecall = {
    x,
    y: recall,
    mode: "lines+markers+text",
    name: "Recall",
    text: numbers,
    textposition: "bottom center",
    marker: { size: 6 },
    line: { color: "#22c55e" },
  };

  return (
    <Plot
      data={[tracePrecision, traceRecall]}
      layout={{
        title: "Overall Precision & Recall over Time",
        xaxis: { title: "Run" },
        yaxis: { title: "Score", range: [0, 1] },
        legend: { orientation: "h" },
        margin: { t: 40, b: 40, l: 50, r: 20 },
      }}
      style={{ width: "100%", height: "350px" }}
      config={{ responsive: true, displayModeBar: false }}
    />
  );
}