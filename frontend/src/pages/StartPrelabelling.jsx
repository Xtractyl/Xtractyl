// StartPrelabellingPage.jsx
import React, { useEffect, useState } from "react";
import ModelDownloadInput from "../components/ModelDownloadInput";
import ModelPicker from "../components/ModelPicker";
import SystemPromptInput from "../components/SystemPromptInput";
import ProjectNameInput from "../components/ProjectNameInput";
import QuestionsAndLabelsPicker from "../components/QuestionsAndLabelsPicker";

const OLLAMA_BASE = "http://localhost:11434";
const API_BASE = "http://localhost:5001";

export default function StartPrelabellingPage() {
  const [model, setModel] = useState(() => localStorage.getItem("ollamaModel") || "");
  const [refreshKey, setRefreshKey] = useState(0);
  const [systemPrompt, setSystemPrompt] = useState(() => localStorage.getItem("xtractylSystemPrompt") || "");
  const [projectName, setProjectName] = useState(() => localStorage.getItem("xtractylProjectName") || "");
  const [qalFile, setQalFile] = useState(() => localStorage.getItem("xtractylQALFile") || "");
  const [busy, setBusy] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");

  // persist selections
  useEffect(() => { try { localStorage.setItem("ollamaModel", model || ""); } catch {} }, [model]);
  useEffect(() => { try { localStorage.setItem("xtractylSystemPrompt", systemPrompt || ""); } catch {} }, [systemPrompt]);
  useEffect(() => { try { localStorage.setItem("xtractylProjectName", projectName || ""); } catch {} }, [projectName]);
  useEffect(() => { try { localStorage.setItem("xtractylQALFile", qalFile || ""); } catch {} }, [qalFile]);

  const handleQalChange = (_project, file) => setQalFile(file);

  const canStart =
    !!projectName && !!model && !!systemPrompt.trim() && !!qalFile;

  const handleStart = async () => {
    if (!canStart) return;
    setBusy(true);
    setStatusMsg("");
    try {
      // TODO: wire to your orchestrator route when ready
      // Example payload—adjust keys to your backend:
      const payload = {
        project_name: projectName,
        model,
        system_prompt: systemPrompt,
        qal_file: qalFile, // file name inside data/projects/<projectName>/
      };

      // Placeholder request (commented until backend is ready):
      // const res = await fetch(`${API_BASE}/prelabel_project`, {
      //   method: "POST",
      //   headers: { "Content-Type": "application/json" },
      //   body: JSON.stringify(payload),
      // });
      // const data = await res.json();
      // if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);

      setStatusMsg("✅ Prelabeling started (stub). Wire to /prelabel_project next.");
    } catch (e) {
      setStatusMsg(`❌ ${e.message || "Failed to start."}`);
    } finally {
      setBusy(false);
    }
  };

  const handleCancel = async () => {
    // TODO: call your cancel endpoint once implemented
    setStatusMsg("ℹ️ Cancel requested (stub).");
  };

  return (
    <div className="p-6 bg-[#e6e2cf] min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Start AI</h1>
      <p className="text-gray-600 mb-6">
        Download a model (if needed), enter your project, pick an installed model, set a system prompt, choose your Questions & Labels JSON, then start prelabeling.
      </p>

      <div className="mb-6">
        <ModelDownloadInput
          ollamaBase={OLLAMA_BASE}
          onDone={() => setRefreshKey((k) => k + 1)}
        />
      </div>

      <div className="space-y-6 bg-[#ede6d6] p-6 rounded shadow max-w-3xl">
        <ProjectNameInput value={projectName} onChange={setProjectName} />
        {/* Helper link to Label Studio projects */}
        <div className="text-sm text-gray-600 -mt-2">
        <div>Forgot your project name?</div>
        <a
            href="http://localhost:8080/projects/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block text-[#6baa56] hover:underline"
        >
            Open Label Studio projects
        </a>
        </div>
        <ModelPicker
          ollamaBase={OLLAMA_BASE}
          selectedModel={model}
          onChange={setModel}
          refreshKey={refreshKey}
        />

        <SystemPromptInput
          value={systemPrompt}
          onChange={setSystemPrompt}
          persistKey="xtractylSystemPrompt"
        />

        <QuestionsAndLabelsPicker
          apiBase={API_BASE}
          projectName={projectName}
          selectedFile={qalFile}
          onChange={handleQalChange}
        />

        {/* One clean summary */}
        <div className="pt-2 text-sm text-gray-600">
          <div>Project: <span className="font-mono">{projectName || "—"}</span></div>
          <div>Model: <span className="font-mono">{model || "—"}</span></div>
          <div>Q&L JSON: <span className="font-mono">{qalFile || "—"}</span></div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <button
            type="button"
            onClick={handleStart}
            disabled={!canStart || busy}
            className={`px-4 py-2 rounded text-white ${
              !canStart || busy
                ? "bg-[#6baa56]/50 cursor-not-allowed"
                : "bg-[#6baa56] hover:bg-[#5b823f]"
            }`}
          >
            {busy ? "Starting…" : "Start Prelabeling"}
          </button>

          <button
            type="button"
            onClick={handleCancel}
            className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300"
          >
            Cancel
          </button>
        </div>

        {statusMsg && <div className="text-sm mt-2">{statusMsg}</div>}
      </div>
    </div>
  );
}