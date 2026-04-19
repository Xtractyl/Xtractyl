// src/components/EvaluateAIPage/ComparisonSelection.jsx
export default function ComparisonSelection({
  projects,
  gtSets,
  loading,
  errorMsg,
  groundtruthProject,
  setGroundtruthProject,
  comparisonProject,
  setComparisonProject,
  onSubmit,
}) {

  const comparisonOptions = projects.filter((name) => !gtSets.includes(name));

  
  return (
    <div className="mt-8">
      <h2 className="text-sm font-medium mb-1">
        Select Groundtruth & Comparison Project
      </h2>

      {loading && <p className="text-sm">Loading projects…</p>}

      {errorMsg && <p className="text-sm text-xtractyl-orange">{errorMsg}</p>}

      {!loading && !errorMsg && projects.length === 0 && (
        <p className="text-sm text-xtractyl-outline/70">
          No projects available for evaluation.
        </p>
      )}

      {!loading && !errorMsg && (gtSets.length > 0 || projects.length > 0) && (
        <>
          {/* Groundtruth Project */}
          <label className="block text-xs font-medium mt-3 mb-1">
            Groundtruth Project
          </label>
          <select
            className="w-full p-2 border border-xtractyl-outline/30 rounded bg-xtractyl-white text-xtractyl-darktext"
            value={groundtruthProject}
            onChange={(e) => setGroundtruthProject(e.target.value)}
          >
            {gtSets.map((name, idx) => (
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
            className="w-full p-2 border border-xtractyl-outline/30 rounded bg-xtractyl-white text-xtractyl-darktext"
            value={comparisonProject}
            onChange={(e) => setComparisonProject(e.target.value)}
          >
            {comparisonOptions.map((name, idx) => (
              <option key={idx} value={name}>
                {name}
              </option>
            ))}
          </select>

          <p className="mt-3 text-xs text-xtractyl-outline">
            Groundtruth: <b>{groundtruthProject}</b>
            <br />
            Comparison: <b>{comparisonProject}</b>
          </p>

          <button
            type="button"
            onClick={onSubmit}
            className="mt-4 inline-flex items-center justify-center px-4 py-2 rounded bg-xtractyl-green text-xtractyl-white text-sm font-medium shadow hover:bg-xtractyl-green/80 transition disabled:opacity-60 disabled:cursor-not-allowed"
            disabled={!groundtruthProject || !comparisonProject}
          >
            Run Evaluation and Save as JSON
          </button>
        </>
      )}
    </div>
  );
}