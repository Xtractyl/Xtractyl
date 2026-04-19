// src/components/EvaluationDriftPage/PlotRegressionControlOverTime.jsx
import Plot from "react-plotly.js";

export default function PlotRegressionControlOverTime({ entries }) {
  if (!entries?.length) return null;

  // Gruppieren nach fixer Konfiguration: system_prompt + questions + labels
  const configKey = (e) =>
    JSON.stringify({
      system_prompt: e.system_prompt || "",
      questions: e.questions || [],
      labels: e.labels || [],
    });

  // Für jede fixe Konfiguration: eine Gruppe
  const groups = {};
  entries.forEach((e) => {
    const key = configKey(e);
    if (!groups[key]) groups[key] = [];
    groups[key].push(e);
  });

  const colors = [
    "#000000", "#22c55e", "#3b82f6", "#a855f7", "#ec4899",
    "#14b8a6", "#eab308", "#ef4444",
  ];

  // Für jede Konfigurationsgruppe: eine Linie pro Modell
  const plots = Object.entries(groups).map(([, groupEntries], groupIdx) => {
    const byModel = {};
    groupEntries.forEach((e) => {
      const model = e.model || "unknown";
      if (!byModel[model]) byModel[model] = [];
      byModel[model].push(e);
    });

    const traces = Object.entries(byModel).map(([model, modelEntries], mi) => {
      const sorted = [...modelEntries].sort((a, b) =>
        String(a.run_at_raw || "").localeCompare(String(b.run_at_raw || ""))
      );
      const numbers = sorted.map((_, i) => String(i + 1));
      const color = colors[mi % colors.length];

      return [
                {
          x: sorted.map((e) => new Date(e.run_at_raw)),
          y: sorted.map((e) => e.metrics?.micro?.recall ?? null),
          mode: "lines+markers+text",
          name: `${model} Recall`,
          text: numbers,
          textposition: "bottom center",
          marker: { size: 6, color },
          line: { color, dash: "solid" },
        },
        {
          x: sorted.map((e) => new Date(e.run_at_raw)),
          y: sorted.map((e) => e.metrics?.micro?.precision ?? null),
          mode: "lines+markers+text",
          name: `${model} Precision`,
          text: numbers,
          textposition: "top center",
          marker: { size: 6, color },
          line: { color, dash: "dot" },
        }
      ];
    });


    return (
      <div key={groupIdx}>
        <p className="text-xs text-xtractyl-outline/60 mb-1">
        </p>
        <Plot
          data={traces.flat()}
          layout={{
            xaxis: { title: "Run" },
            yaxis: { title: "Score", range: [0, 1] },
            legend: { orientation: "h" },
            margin: { t: 40, b: 40, l: 50, r: 20 },
            height: 400,
          }}
          style={{ width: "100%", height: "450px" }}
      config={{ responsive: false, displayModeBar: false }}

        />
      </div>
    );
  });

  return <div className="space-y-6">{plots}</div>;
}