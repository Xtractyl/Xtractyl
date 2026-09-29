// src/components/StartPrelabellingPage/PrelabellingReadyProjectSelect.jsx
import { useEffect, useState } from "react";
import { getProjectsReadyForPrelabelling } from "../../api/StartPrelabellingPage/api.js";

export default function PrelabellingReadyProjectSelect({ selected, onChange }) {
  const [projects, setProjects] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    getProjectsReadyForPrelabelling()
      .then((list) => {
        setProjects(list);
        setLoaded(true);
      })
      .catch((e) => {
        setProjects([]);
        setErr(e.message || "Failed to load projects.");
      });
  }, []);

  // A project name kept in the shared context may not be startable here (e.g. it was
  // just prelabelled); clear it so a hidden, stale value can't enable the start button.
  useEffect(() => {
    if (loaded && selected && !projects.includes(selected)) onChange("");
  }, [loaded, projects, selected, onChange]);

  return (
    <div>
      <label className="block font-medium mb-1">
        Select project (tasks uploaded, prelabelling not yet (successfully) run)
      </label>
      <select
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        required
        className="w-full p-2 border rounded"
      >
        <option value="">-- Select Project --</option>
        {projects.map((p) => (
          <option key={p} value={p}>
            {p}
          </option>
        ))}
      </select>
      {err && <div className="text-sm text-xtractyl-orange mt-1">{err}</div>}
    </div>
  );
}
