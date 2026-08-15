import { useEffect, useState } from "react";
import { fetchRegressionView } from "../../api/EvaluationDriftPage/api.js";

export default function RegressionTab({ projectName, scope }) {
  const [entries, setEntries] = useState([]);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    if (!projectName) {
      setEntries([]);
      return;
    }
    fetchRegressionView(projectName, scope).then((data) => {
      setEntries(data.entries || []);
    });
  }, [projectName, scope]);

  if (!projectName)
    return <p className="text-sm text-xtractyl-outline/70">Please select a project.</p>;

  if (!entries.length)
    return (
      <p className="text-sm text-xtractyl-outline/70">
        No regression series yet (at least 2 runs with the identical
        configuration against the same document set) for this project.
      </p>
    );

  return (
    <div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xtractyl-outline/70">
            <th className="pr-4">Ground Truth</th>
            <th className="pr-4">Time</th>
            <th className="pr-4">Project</th>
            <th className="pr-4">Model</th>
            <th className="pr-4">Precision</th>
            <th className="pr-4">Recall</th>
            <th>F1</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e, i) => {
            const perLabel = e.metrics?.per_label || {};
            const labelNames = Object.keys(perLabel);
            const isExpanded = expanded === i;
            return (
              <>
                <tr
                  key={i}
                  className="cursor-pointer hover:bg-xtractyl-offwhite"
                  onClick={() => setExpanded(isExpanded ? null : i)}
                >
                  <td className="pr-4">{e.groundtruth_project}</td>
                  <td className="pr-4">
                    {e.run_at_raw ? new Date(e.run_at_raw).toLocaleString() : "—"}
                  </td>
                  <td className="pr-4">{e.comparison_project || "—"}</td>
                  <td className="pr-4">{e.model || "—"}</td>
                  <td className="pr-4">{e.metrics?.micro?.precision?.toFixed(3) ?? "—"}</td>
                  <td className="pr-4">{e.metrics?.micro?.recall?.toFixed(3) ?? "—"}</td>
                  <td>{e.metrics?.micro?.f1?.toFixed(3) ?? "—"}</td>
                </tr>
                {isExpanded && labelNames.length > 0 && (
                  <tr key={`${i}-detail`}>
                    <td colSpan={7} className="bg-xtractyl-offwhite/50 px-4 py-2">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="text-left text-xtractyl-outline/70">
                            <th className="pr-4">Label</th>
                            <th className="pr-4">Precision</th>
                            <th className="pr-4">Recall</th>
                            <th>F1</th>
                          </tr>
                        </thead>
                        <tbody>
                          {labelNames.map((label) => (
                            <tr key={label}>
                              <td className="pr-4">{label}</td>
                              <td className="pr-4">
                                {perLabel[label].precision?.toFixed(3) ?? "—"}
                              </td>
                              <td className="pr-4">
                                {perLabel[label].recall?.toFixed(3) ?? "—"}
                              </td>
                              <td>{perLabel[label].f1?.toFixed(3) ?? "—"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </td>
                  </tr>
                )}
              </>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}