// src/components/UploadTasks/UploadTasksCard.jsx
import React, { useState } from "react";
import ProjectNameInput from "../shared/ProjectNameInput";
import HtmlFolderSelect from "./HTMLFolderSelect";
import { uploadTasks } from "../../api/UploadTasksPage/api.js";

const LS_BASE = import.meta.env.VITE_LS_BASE || "http://localhost:8080";

export default function UploadTasksCard({ apiToken }) {
  const [projectName, setProjectName] = useState("");
  const [htmlFolder, setHtmlFolder] = useState("");
  const [localToken, setLocalToken] = useState(apiToken || "");
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);

  const handleUpload = async () => {
    if (!projectName || !htmlFolder || !localToken) {
      alert("Please provide all fields.");
      return;
    }
  
    try {
      setBusy(true);
      setStatus(null);
  
      const result = await uploadTasks({
        projectName,
        token: localToken,
        htmlFolder,
      });
  
      console.log("✅ Upload success:", result);
      setStatus("✅ Tasks uploaded successfully.");
    } catch (error) {
      console.error("❌ Upload error:", error);
      setStatus(`❌ Upload failed. ${error.message || "See console for details."}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="p-6 bg-[#e6e2cf] min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Upload Tasks</h1>
      <p className="text-gray-600 mb-6">
        Select your project, API token, and HTML folder to upload tasks.
      </p>

      <div className="space-y-6 bg-[#ede6d6] p-6 rounded shadow max-w-xl">
        <ProjectNameInput value={projectName} onChange={setProjectName} />
        <HtmlFolderSelect selected={htmlFolder} onChange={setHtmlFolder} />

        {/* Token helper link */}
        <div>
          <a
            href={`${LS_BASE}/user/account/legacy-token`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-[#db7127] text-white text-base font-medium px-5 py-2 rounded shadow hover:bg-orange-600 transition"
          >
            Get your legacy token
          </a>
          <p className="mt-2 text-sm text-gray-500">
            Return here after copying the token from Label Studio.
          </p>
          <p className="mt-1 text-sm text-gray-500">
            ⚠️ If you see no legacy token there, go to{" "}
            <a
              href={`${LS_BASE}/organization`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#6baa56] hover:underline"
            >
              {LS_BASE}/organization
            </a>{" "}
            and enable it via the API Tokens settings.
          </p>
        </div>

        {/* Token Input */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Label Studio Token
          </label>
          <input
            type="text"
            value={localToken}
            onChange={(e) => setLocalToken(e.target.value)}
            placeholder={localToken || "Enter your Label Studio token"}
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <button
          onClick={handleUpload}
          disabled={busy}
          className={`px-4 py-2 rounded text-white ${
            busy
              ? "bg-[#6baa56]/50 cursor-not-allowed"
              : "bg-[#6baa56] hover:bg-[#5b823f]"
          }`}
        >
          {busy ? "Uploading…" : "Upload HTML Tasks"}
        </button>

        {/* Helper link to Label Studio projects */}
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