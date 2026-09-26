//src/components/GetResultsPage/ResultsReadyProjectSelect.jsx
import { useEffect, useState } from "react";
import { getProjectsReadyForResults } from "../../api/GetResultsPage/api.js";

export default function ResultsReadyProjectSelect({ selected, onChange }) {
  const [projects, setProjects] = useState([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    getProjectsReadyForResults()
      .then(setProjects)
      .catch((e) => {
        setProjects([]);
        setErr(e.message || "Failed to load projects.");
      });
  }, []);

  return (
    <div className="flex flex-col flex-1">
      <label className="font-semibold mb-2">Project name</label>
      <select
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        required
        className="border border-xtractyl-outline/30 rounded-md text-sm px-3 py-2 outline-none w-full focus:ring-2 focus:ring-xtractyl-lightgreen bg-white"
      >
        <option value="">-- Select Project --</option>
        {projects.map((p, i) => {
          const isGt = p.startsWith("Evaluation_Sets_Do_Not_Delete/");
          return (
            <option key={i} value={p}>{isGt ? `GT: ${p.split("/").pop()}` : p}</option>
          );
        })}
      </select>
      {err && <div className="text-sm text-xtractyl-orange mt-1">{err}</div>}
    </div>
  );
}