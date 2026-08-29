// src/components/EvaluateAIPage/SaveAsGtSet.jsx
import { useEffect, useState } from "react";
import { saveAsGtSet, getProjectsReadyForGroundtruth } from "../../api/EvaluateAIPage/api.js";
 

export default function SaveAsGtSet({ apiToken, onSuccess }) {
  const [candidates, setCandidates] = useState([]);
  const [loadError, setLoadError] = useState("");
  const [sourceProject, setSourceProject] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const loadCandidates = () => {
    getProjectsReadyForGroundtruth()
      .then(setCandidates)
      .catch((e) => setLoadError(e.message || "Failed to load projects."));
  };

  useEffect(() => {
    loadCandidates();
  }, []);

  const handleSubmit = async (scope) => {
    if (!sourceProject) return;
    setLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      await saveAsGtSet(apiToken, sourceProject, scope);
      setSuccessMsg(`"${sourceProject}" successfully saved as ${scope} GT set.`);
      setSourceProject("");
      loadCandidates();
      onSuccess?.();
    } catch (e) {
      setErrorMsg(e?.message || "Failed to save as GT set.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-8 border border-xtractyl-outline/20 rounded-lg p-4 bg-xtractyl-offwhite">
      <h2 className="text-sm font-semibold mb-3 text-xtractyl-outline">
        Save Project as Ground Truth Set
      </h2>

      <label className="block text-xs font-medium mb-1">Source Project</label>
      <select
        value={sourceProject}
        onChange={(e) => setSourceProject(e.target.value)}
        className="w-full p-2 border border-xtractyl-outline/30 rounded bg-xtractyl-white text-xtractyl-darktext text-sm mb-3"
      >
        <option value="">-- Select Project --</option>
        {candidates.map((p) => (
          <option key={p} value={p}>{p}</option>
        ))}
      </select>
      {loadError && (
        <p className="text-sm text-xtractyl-orange mb-2">{loadError}</p>
      )}
      {errorMsg && (
        <p className="text-sm text-xtractyl-orange mb-2">{errorMsg}</p>
      )}
      {successMsg && (
        <p className="text-sm text-xtractyl-green mb-2">{successMsg}</p>
      )}

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => handleSubmit("external")}
          disabled={!sourceProject || loading}
          className="px-4 py-2 rounded bg-xtractyl-green text-xtractyl-white text-sm font-medium shadow hover:bg-xtractyl-green/80 transition disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? "Saving…" : "Save as External GT"}
        </button>
        <button
          type="button"
          onClick={() => handleSubmit("internal")}
          disabled={!sourceProject || loading}
          className="px-4 py-2 rounded bg-xtractyl-outline text-xtractyl-white text-sm font-medium shadow hover:bg-xtractyl-outline/80 transition disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? "Saving…" : "Save as Internal GT"}
        </button>
      </div>

    </div>
  );
}