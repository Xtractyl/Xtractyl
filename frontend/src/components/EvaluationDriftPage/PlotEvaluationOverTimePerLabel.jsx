// src/components/EvaluationDriftPage/PlotEvaluationOverTimePerLabel.jsx
import Plot from "react-plotly.js";

export default function PlotEvaluationOverTimePerLabel({ entries }) {
  if (!entries?.length) return null;
  
  const sorted = [...entries].sort((a, b) =>
    String(a.run_at_raw || "").localeCompare(String(b.run_at_raw || ""))
  );

  const labelSet = new Set();
  sorted.forEach((e) => {
    Object.keys(e.metrics?.per_label || {}).forEach((l) => labelSet.add(l));
  });
  const labels = [...labelSet];
  const legendY = 1.05 + labels.length * 0.08;
  const plotHeight = 400 + labels.length * 20;

  const colors = [
    "#000000", "#22c55e", "#3b82f6", "#a855f7", "#ec4899",
    "#14b8a6", "#eab308", "#ef4444",
  ];

  const numbers = sorted.map((e) => String(e.number));
  const x = sorted.map((e) => e.number);

  const traces = labels.flatMap((label, li) => {
    const color = colors[li % colors.length];
    const precision = sorted.map(
      (e) => e.metrics?.per_label?.[label]?.precision ?? null
    );
    const recall = sorted.map(
      (e) => e.metrics?.per_label?.[label]?.recall ?? null
    );

    return [
            {
        x,
        y: recall,
        mode: "lines+markers+text",
        name: `${label} Recall`,
        text: numbers,
        textposition: "bottom center",
        marker: { size: 6, color },
        line: { color, dash: "solid" },
      },
      
      {
        x,
        y: precision,
        mode: "lines+markers+text",
        name: `${label} Precision`,
        text: numbers,
        textposition: "top center",
        marker: { size: 6, color },
        line: { color, dash: "dot" },
      },
    ];
  });

  return (
    <Plot
      data={traces}
      layout={{
        xaxis: { title: "Run",
          tickmode: "array",
          tickvals: sorted.map((e) => e.number),
          ticktext: sorted.map((e) => new Date(e.run_at_raw).toLocaleString()),
          tickangle: 45,
          tickfont: { size: 12 },
        },
        yaxis: { title: "Score", range: [0, 1] },
        legend: { orientation: "h", x: 0, y: legendY },
        margin: { t: 40, b: 120, l: 50, r: 20 },
        height: plotHeight,
      }}
      style={{ width: "100%", height: `${plotHeight + 50}px` }}
      config={{ responsive: false, displayModeBar: false }}
    />
  );
}