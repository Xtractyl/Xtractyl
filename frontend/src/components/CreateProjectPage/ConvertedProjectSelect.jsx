//src/components/CreateProjectPage/ConvertedProjectSelect.jsx
import { useEffect, useState } from "react";
import { getProjectsWithoutLabelStudioId } from "../../api/CreateProjectPage/api.js";

export default function ConvertedProjectSelect({ selected, onChange }) {
  const [projects, setProjects] = useState([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    getProjectsWithoutLabelStudioId()
      .then(setProjects)
      .catch((e) => {
        setProjects([]);
        setErr(e.message || "Failed to load projects.");
      });
  }, []);

  return (
    <div>
      <label className="block font-medium mb-1">
        Select converted project (not yet created in Label Studio)
      </label>
      <select
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        required
        className="w-full p-2 border rounded"
      >
        <option value="">-- Select Project --</option>
        {projects.map((p, i) => (
          <option key={i} value={p}>{p}</option>
        ))}
      </select>
      {err && <div className="text-sm text-xtractyl-orange mt-1">❌ {err}</div>}
    </div>
  );
}