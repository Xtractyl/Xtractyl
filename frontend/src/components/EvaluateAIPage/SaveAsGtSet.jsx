// src/components/EvaluateAIPage/SaveAsGtSet.jsx
import { useState } from "react";
import { saveAsGtSet } from "../../api/EvaluateAIPage/api.js";

export default function SaveAsGtSet({ apiToken, projects, gtSets }) {
  const [sourceProject, setSourceProject] = useState("");
  const [gtSetName, setGtSetName] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const candidates = projects.filter((p) => !gtSets.includes(p));

  const handleSubmit = async () => {
    if (!sourceProject || !gtSetName) return;
    setLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const result = await saveAsGtSet(apiToken, sourceProject, gtSetName);
      setSuccessMsg(`GT set "${result.gt_set_name}" successfully created.`);
      setGtSetName("");
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

      <label className="block text-xs font-medium mb-1">New GT Set Name</label>
      <input
        type="text"
        value={gtSetName}
        onChange={(e) => setGtSetName(e.target.value)}
        placeholder="Enter a name for the new GT set"
        className="w-full border border-xtractyl-outline/30 rounded px-3 py-2 bg-xtractyl-white text-xtractyl-darktext text-sm mb-3"
      />

      {errorMsg && (
        <p className="text-sm text-xtractyl-orange mb-2">{errorMsg}</p>
      )}
      {successMsg && (
        <p className="text-sm text-xtractyl-green mb-2">{successMsg}</p>
      )}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={!sourceProject || !gtSetName || loading}
        className="px-4 py-2 rounded bg-xtractyl-green text-xtractyl-white text-sm font-medium shadow hover:bg-xtractyl-green/80 transition disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {loading ? "Saving…" : "Save as GT Set"}
      </button>
    </div>
  );
}