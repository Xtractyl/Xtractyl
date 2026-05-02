// src/components/UploadTasks/UploadTasksCard.jsx
import { useState } from "react";
import ProjectNameInput from "../shared/ProjectNameInput";
import HtmlFolderSelect from "./HTMLFolderSelect";
import { uploadTasks } from "../../api/UploadTasksPage/api.js";
import { useAppContext } from "../../context/AppContext";
import TokenLink from "../shared/TokenLink";

const LS_BASE = import.meta.env.VITE_LS_BASE || "http://localhost:8080";

export default function UploadTasksCard() {
  const { token, projectName, saveToken, saveProjectName } = useAppContext();
  const [htmlFolder, setHtmlFolder] = useState("");
  const [statusMsg, setStatusMsg] = useState("");
  const [busy, setBusy] = useState(false);


  const handleUpload = async () => {
    if (!projectName || !htmlFolder || !token) {
      setStatusMsg("❌ Please provide all fields.");
      return;
    }

    try {
      setBusy(true);
      setStatusMsg(null);

      await uploadTasks({
        projectName,
        token,
        htmlFolder,
      });
      setStatusMsg("✅ Tasks uploaded successfully.");
    } catch (e) {
     setStatusMsg(`❌ ${e.message || "Upload failed."}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="p-6 bg-xtractyl-background min-h-screen text-xtractyl-darktext">
      <h1 className="text-2xl font-semibold mb-4">Upload Tasks</h1>
      <p className=" text-xtractyl-outline/70 mb-6">
        Select your project, API token, and HTML folder to upload tasks.
      </p>

      <div className="space-y-6 bg-xtractyl-offwhite p-6 rounded shadow">
        <ProjectNameInput value={projectName} onChange={saveProjectName} />
        <HtmlFolderSelect selected={htmlFolder} onChange={setHtmlFolder} />

        {/* Token helper link */}
        <div>
          <TokenLink />
        </div>

        {/* Token Input */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Label Studio Token
          </label>
          <input
            key={token ?? "empty"}   
            type="password"
            value={token}
            onChange={(e) => saveToken(e.target.value)}
            placeholder={token || "Enter your Label Studio token"}
            className="w-full border border-xtractyl-outline/30 rounded px-3 py-2 bg-xtractyl-white text-xtractyl-darktext"
          />
        </div>

        <button
          onClick={handleUpload}
          disabled={busy}
          className={`px-4 py-2 rounded text-xtractyl-white ${
            busy
              ? "bg-xtractyl-green/50 cursor-not-allowed"
              : "bg-xtractyl-green hover:bg-xtractyl-green/80 transition"
          }`}
        >
          {busy ? "Uploading…" : "Upload HTML Tasks"}
        </button>

        {/* Helper link to Label Studio projects */}
        <div className="pt-2 border-t border-xtractyl-outline/20">
          <div className="text-sm font-medium mb-1">
            Forgot your project name? Want to check the task upload?
          </div>
          <a
            href={`${LS_BASE}/projects?pag=&page=1`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block text-xtractyl-green hover:underline"
          >
            Open Label Studio projects
          </a>
        </div>

        {statusMsg && <p className="mt-4 text-sm">{statusMsg}</p>}
      </div>
    </div>
  );
}