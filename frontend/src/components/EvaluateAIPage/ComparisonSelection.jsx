// src/components/EvaluateAIPage/ComparisonSelection.jsx
export default function ComparisonSelection({
  projects,
  loading,
  errorMsg,
  compatibleGtSets,
  compatibleLoading,
  compatibleError,
  groundtruthProject,
  setGroundtruthProject,
  comparisonProject,
  setComparisonProject,
  onSubmit,
}) {
  return (
    <div className="mt-8">
      <h2 className="text-sm font-medium mb-1">Select Groundtruth & Comparison Project</h2>

      {loading && <p className="text-sm">Loading projects…</p>}

      {errorMsg && <p className="text-sm text-xtractyl-orange">{errorMsg}</p>}

      {!loading && !errorMsg && projects.length === 0 && (
        <p className="text-sm text-xtractyl-outline/70">No projects available for evaluation.</p>
      )}

      {!loading && !errorMsg && projects.length > 0 && (
        <>
          {/* Comparison Project */}
          <label className="block text-xs font-medium mt-4 mb-1">Comparison Project</label>
          <select
            className="w-full p-2 border border-xtractyl-outline/30 rounded bg-xtractyl-white text-xtractyl-darktext"
            value={comparisonProject}
            onChange={(e) => setComparisonProject(e.target.value)}
          >
            {projects.map((name, idx) => (
              <option key={idx} value={name}>
                {name}
              </option>
            ))}
          </select>

          {/* groundtruth project, restricted to sets that already have a
              computed evaluation for the comparison project selected above */}
          <label className="block text-xs font-medium mt-3 mb-1">
            Groundtruth Project (those available for the Comparison Project selected above)
          </label>
          <select
            className="w-full p-2 border border-xtractyl-outline/30 rounded bg-xtractyl-white text-xtractyl-darktext"
            value={groundtruthProject}
            onChange={(e) => setGroundtruthProject(e.target.value)}
          >
            {compatibleGtSets.map((name, idx) => (
              <option key={idx} value={name}>
                {name}
              </option>
            ))}
          </select>

          {compatibleLoading && <p className="mt-1 text-xs">Loading groundtruth projects…</p>}

          {compatibleError && (
            <p className="mt-1 text-xs text-xtractyl-orange">{compatibleError}</p>
          )}

          {!compatibleLoading && !compatibleError && compatibleGtSets.length === 0 && (
            <p className="mt-1 text-xs text-xtractyl-outline/70">
              No groundtruth project available for this comparison project.
            </p>
          )}
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
            Show Evaluation
          </button>
        </>
      )}
    </div>
  );
}
