//src/components/UploadTasksPage/UploadReadyProjectSelect.jsx
import { useEffect, useState } from "react";
import { getProjectsReadyForUpload } from "../../api/UploadTasksPage/api.js";

export default function UploadReadyProjectSelect({ selected, onChange }) {
  const [projects, setProjects] = useState([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    getProjectsReadyForUpload()
      .then(setProjects)
      .catch((e) => {
        setProjects([]);
        setErr(e.message || "Failed to load projects.");
      });
  }, []);

  return (
    <div>
      <label className="block font-medium mb-1">
        Select project (Tasks will be sent to Label Studio)
      </label>
      <select
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        required
        className="w-full p-2 border rounded"
      >
        <option value="">-- Select Project --</option>
        {projects.map((p, i) => {
          const isGt = p.startsWith("Evaluation_Sets_Do_Not_Delete/");
          return (
            <option key={i} value={p}>{isGt ? `🔒 GT: ${p.split("/").pop()}` : p}</option>
          );
        })}
      </select>
      {err && <div className="text-sm text-xtractyl-orange mt-1">❌ {err}</div>}
    </div>
  );
}