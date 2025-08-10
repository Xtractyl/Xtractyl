// src/components/UploadTasks/UploadTasksCard.jsx
import React, { useState } from "react";
import ProjectNameInput from "./ProjectNameInput";
import HtmlFolderSelect from "./HTMLFolderSelect";

const ORCH_BASE = "http://localhost:5001";  // Orchestrator backend
const LS_BASE   = "http://localhost:8080";  // Label Studio

export default function UploadTasksCard({ apiToken }) {
  const [projectName, setProjectName] = useState("");
  const [htmlFolder, setHtmlFolder] = useState("");
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);

  const handleUpload = async () => {
    if (!projectName || !htmlFolder || !apiToken) {
      alert("Please provide all fields.");
      return;
    }

    try {
      setBusy(true);
      setStatus(null);

      const response = await fetch(`${ORCH_BASE}/upload_tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_name: projectName,
          token: apiToken,
          html_folder: htmlFolder,
        }),
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const result = await response.json();
      console.log("✅ Upload success:", result);
      setStatus("✅ Tasks uploaded successfully.");
    } catch (error) {
      console.error("❌ Upload error:", error);
      setStatus("❌ Upload failed. See console for details.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="p-6 bg-[#e6e2cf] min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Upload Tasks</h1>
      <p className="text-gray-600 mb-6">
        Select your project and HTML folder to upload tasks.
      </p>

      <div className="space-y-6 bg-[#ede6d6] p-6 rounded shadow max-w-xl">
        <ProjectNameInput value={projectName} onChange={setProjectName} />
        <HtmlFolderSelect selected={htmlFolder} onChange={setHtmlFolder} />

        <button
          onClick={handleUpload}
          disabled={busy}
          className={`px-4 py-2 rounded text-white ${
            busy ? "bg-[#6baa56]/50 cursor-not-allowed" : "bg-[#6baa56] hover:bg-[#5b823f]"
          }`}
        >
          {busy ? "Uploading…" : "Upload HTML Tasks"}
        </button>

        {/* Helper link to Label Studio */}
        <div className="pt-2 border-t border-[#d8cfbd]">
          <div className="text-sm font-medium mb-1">
            Forgot your project name? Want to check the task upload?
          </div>
          <a
            href={`${LS_BASE}/projects?pag=&page=1`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block text-[#6baa56] hover:underline"
          >
            Open Label Studio projects
          </a>
        </div>

        {status && <p className="mt-4 text-sm">{status}</p>}
      </div>
    </div>
  );
}