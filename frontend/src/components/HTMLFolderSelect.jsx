import React, { useEffect, useState } from "react";

// === API Base URLs ===
const ORCH_BASE = "http://localhost:5001"; // Orchestrator backend

export default function HtmlFolderSelect({ selected, onChange }) {
  const [folders, setFolders] = useState([]);

  useEffect(() => {
    fetch(`${ORCH_BASE}/list_html_subfolders`)
      .then((res) => res.json())
      .then((data) => setFolders(data))
      .catch(() => setFolders([]));
  }, []);

  return (
    <div>
      <label className="block font-medium mb-1">
        Select HTML (Folder content will be sent to Label Studio)
      </label>
      <select
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        required
        className="w-full p-2 border rounded"
      >
        <option value="">-- Select Folder --</option>
        {folders.map((f, i) => (
          <option key={i} value={f}>
            {f}
          </option>
        ))}
      </select>
    </div>
  );
}