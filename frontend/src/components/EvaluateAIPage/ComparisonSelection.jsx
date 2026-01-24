// src/components/EvaluateAIPage/ComparisonSelection.jsx
import React from "react";

export default function ComparisonSelection({
  projects,
  loading,
  errorMsg,
  groundtruthProject,
  setGroundtruthProject,
  comparisonProject,
  setComparisonProject,
  onSubmit,
}) {

  const SPECIAL = "Evaluation_Set_Do_Not_Delete";
  const comparisonOptions = projects.filter((name) => name !== SPECIAL);
  
  return (
    <div className="mt-8">
      <h2 className="text-sm font-medium mb-1">
        Select Groundtruth & Comparison Project
      </h2>

      {loading && <p className="text-sm">Loading projects…</p>}

      {errorMsg && <p className="text-sm text-red-600">{errorMsg}</p>}

      {!loading && !errorMsg && projects.length === 0 && (
        <p className="text-sm text-gray-600">
          No projects available for evaluation.
        </p>
      )}

      {!loading && !errorMsg && projects.length > 0 && (
        <>
          {/* Groundtruth Project */}
          <label className="block text-xs font-medium mt-3 mb-1">
            Groundtruth Project
          </label>
          <select
            className="w-full p-2 border rounded bg-xtractyl-white"
            value={groundtruthProject}
            onChange={(e) => setGroundtruthProject(e.target.value)}
          >
            {projects.map((name, idx) => (
              <option key={idx} value={name}>
                {name}
              </option>
            ))}
          </select>

          {/* Comparison Project */}
          <label className="block text-xs font-medium mt-4 mb-1">
            Comparison Project
          </label>
          <select
            className="w-full p-2 border rounded bg-xtractyl-white"
            value={comparisonProject}
            onChange={(e) => setComparisonProject(e.target.value)}
          >
            {comparisonOptions.map((name, idx) => (
              <option key={idx} value={name}>
                {name}
              </option>
            ))}
          </select>

          <p className="mt-3 text-xs text-gray-700">
            Groundtruth: <b>{groundtruthProject}</b>
            <br />
            Comparison: <b>{comparisonProject}</b>
          </p>

          <button
            type="button"
            onClick={onSubmit}
            className="mt-4 inline-flex items-center justify-center px-4 py-2 rounded bg-xtractyl-green text-white text-sm font-medium shadow hover:bg-xtractyl-green transition disabled:opacity-60 disabled:cursor-not-allowed"
            disabled={!groundtruthProject || !comparisonProject}
          >
            Run Evaluation and Save as JSON
          </button>
        </>
      )}
    </div>
  );
}