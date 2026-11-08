// /src/components/EvaluationDriftPage/EvaluationDriftView.jsx
import { useState } from "react";
import { useEvaluatedProjects } from "../../hooks/EvaluationDriftPage/useEvaluatedProjects.js";
import ComparisonTab from "./ComparisonTab.jsx";
import RegressionTab from "./RegressionTab.jsx";
import DriftTab from "./DriftTab.jsx";

export default function EvaluationDriftView() {
  const [activeTab, setActiveTab] = useState("comparison"); // "comparison" | "regression" | "drift"
  const [selectedProject, setSelectedProject] = useState("");
  const [scope, setScope] = useState("external");
  const { projects, loading, errorMsg } = useEvaluatedProjects();

  if (loading) return <div className="text-sm text-xtractyl-outline/70">Loading…</div>;

  if (errorMsg) return <div className="text-sm text-xtractyl-orange">{errorMsg}</div>;

  if (!projects.length)
    return <div className="text-sm text-xtractyl-outline/70">No evaluated projects yet.</div>;

  return (
    <div className="space-y-6">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setScope("external")}
          className={`px-3 py-1 rounded text-sm ${scope === "external" ? "font-semibold bg-xtractyl-offwhite" : ""}`}
        >
          External
        </button>
        <button
          type="button"
          onClick={() => setScope("internal")}
          className={`px-3 py-1 rounded text-sm ${scope === "internal" ? "font-semibold bg-xtractyl-offwhite" : ""}`}
        >
          Internal
        </button>
      </div>

      <div>
        <label className="block text-xs font-medium mb-1">Project</label>
        <select
          className="w-full p-2 border border-xtractyl-outline/30 rounded"
          value={selectedProject}
          onChange={(e) => setSelectedProject(e.target.value)}
        >
          <option value="">Choose a Project.</option>
          {projects.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => setActiveTab("comparison")}
          className={activeTab === "comparison" ? "font-semibold" : ""}
        >
          Comparison
        </button>
        <button
          onClick={() => setActiveTab("regression")}
          className={activeTab === "regression" ? "font-semibold" : ""}
        >
          Regression
        </button>
        <button
          onClick={() => setActiveTab("drift")}
          className={activeTab === "drift" ? "font-semibold" : ""}
        >
          Drift
        </button>
      </div>

      {activeTab === "comparison" && <ComparisonTab projectName={selectedProject} scope={scope} />}
      {activeTab === "regression" && <RegressionTab projectName={selectedProject} scope={scope} />}
      {activeTab === "drift" && <DriftTab projectName={selectedProject} scope={scope} />}
    </div>
  );
}
