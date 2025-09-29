import React, { useEffect, useState } from "react";
import ModelDownloadInput from "./ModelDownloadInput";
import ModelPicker from "./ModelPicker";
import SystemPromptInput from "./SystemPromptInput";
import ProjectNameInput from "../shared/ProjectNameInput";
import QuestionsAndLabelsPicker from "./QuestionsAndLabelsPicker";

const OLLAMA_BASE = import.meta.env.VITE_OLLAMA_BASE || "http://localhost:11434";
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";
const LS_BASE = import.meta.env.VITE_LS_BASE || "http://localhost:8080";

export default function StartPrelabellingCard({ apiToken }) {
  const [model, setModel] = useState(() => localStorage.getItem("ollamaModel") || "");
  const [refreshKey, setRefreshKey] = useState(0);
  const [systemPrompt, setSystemPrompt] = useState(
    () => localStorage.getItem("xtractylSystemPrompt") || ""
  );
  const [projectName, setProjectName] = useState(
    () => localStorage.getItem("xtractylProjectName") || ""
  );
  const [qalFile, setQalFile] = useState(
    () => localStorage.getItem("xtractylQALFile") || ""
  );
  const [questionsAndLabels, setQuestionsAndLabels] = useState({});
  const [preJobId, setPreJobId] = useState(
    () => localStorage.getItem("prelabelJobId") || ""
  );
  const [preStatus, setPreStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [token, setToken] = useState(apiToken || ""); 

  useEffect(() => { try { localStorage.setItem("ollamaModel", model || ""); } catch {} }, [model]);
  useEffect(() => { try { localStorage.setItem("xtractylSystemPrompt", systemPrompt || ""); } catch {} }, [systemPrompt]);
  useEffect(() => { try { localStorage.setItem("xtractylProjectName", projectName || ""); } catch {} }, [projectName]);
  useEffect(() => { try { localStorage.setItem("xtractylQALFile", qalFile || ""); } catch {} }, [qalFile]);

  const handleQalChange = (_project, file, json) => {
    setQalFile(file);
    setQuestionsAndLabels(json);
  };

  const canStart = !!projectName && !!model && !!systemPrompt.trim() && !!qalFile && !!token && !preJobId;

  const handleStart = async () => {
    if (!canStart) return;
    setBusy(true);
    setStatusMsg("");
    try {
      const payload = {
        project_name: projectName,
        model,
        system_prompt: systemPrompt,
        qal_file: qalFile,
        token,
        questions_and_labels: questionsAndLabels 
      };
      const res = await fetch(`${ORCH_BASE}/prelabel_project`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);
      setStatusMsg("✅ Prelabeling finished.");
    } catch (e) {
      setStatusMsg(`❌ ${e.message || "Failed to start."}`);
    } finally {
      setBusy(false);
    }
  };

  const handleCancel = async () => {
    if (!preJobId) return;
    try {
      const res = await fetch(`${ORCH_BASE}/prelabel/cancel/${preJobId}`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);
      setStatusMsg(
        data.status === "cancel_requested" ? "🛑 Cancel requested." : "ℹ️ Already finished."
      );
    } catch (e) {
      setStatusMsg(`❌ ${e.message || "Cancel failed."}`);
    }
  };

  useEffect(() => {
    if (!preJobId) return;
    let cancelled = false;
    let timer = null;
    const schedule = (ms = 1500) => {
      if (!cancelled) timer = setTimeout(tick, ms);
    };
    const tick = async () => {
      try {
        const res = await fetch(`${ORCH_BASE}/prelabel/status/${preJobId}`);
        if (!res.ok) {
          if (res.status === 404) {
            localStorage.removeItem("prelabelJobId");
            setPreJobId("");
            setPreStatus(null);
            return;
          }
          return schedule();
        }
        const s = await res.json();
        setPreStatus(s);
        if (["done", "error", "cancelled"].includes(s.state)) {
          localStorage.removeItem("prelabelJobId");
          setPreJobId("");
          return;
        }
        schedule();
      } catch {
        schedule();
      }
    };
    tick();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [preJobId]);

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
        {/* Project name */}
        <ProjectNameInput value={projectName} onChange={setProjectName} />
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

        {/* Token helper + Eingabe */}
        <div>
          <a
            href={`${LS_BASE}/user/account`}
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

        <div className="mt-3">
          <label className="block text-sm font-medium mb-1">Label Studio Token</label>
          <input
            type="text"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Paste your legacy API token"
            className="w-full border rounded px-3 py-2"
            autoComplete="off"
            spellCheck={false}
          />
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
          apiBase={ORCH_BASE}
          projectName={projectName}
          selectedFile={qalFile}
          onChange={handleQalChange}
        />

        <div className="pt-2 text-sm text-gray-600">
          <div>Project: <span className="font-mono">{projectName || "—"}</span></div>
          <div>Model: <span className="font-mono">{model || "—"}</span></div>
          <div>Q&L JSON: <span className="font-mono">{qalFile || "—"}</span></div>
        </div>

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
            disabled={!preJobId}
            className={`px-4 py-2 rounded ${
              preJobId
                ? "bg-red-600 text-white hover:bg-red-700"
                : "bg-gray-200 text-gray-700 cursor-not-allowed"
            }`}
          >
            Cancel
          </button>
        </div>

        {(preJobId || preStatus) && (
          <div className="mt-4 bg-[#cdc0a3] p-4 rounded">
            <div className="font-medium mb-1">
              Status: {preStatus?.state || "queued"}{" "}
              {typeof preStatus?.progress === "number"
                ? `— ${Math.round((preStatus.progress || 0) * 100)}%`
                : ""}
            </div>
            <div className="w-full h-2 bg-gray-200 rounded">
              <div
                className="h-2 bg-[#6baa56] rounded"
                style={{ width: `${Math.round((preStatus?.progress || 0) * 100)}%` }}
              />
            </div>
            {preStatus?.message && <div className="text-sm mt-2">{preStatus.message}</div>}
            {preJobId && (
              <div className="text-xs text-gray-600 mt-1">
                Job ID: <span className="break-all">{preJobId}</span>
              </div>
            )}
          </div>
        )}

        {statusMsg && <div className="text-sm mt-2">{statusMsg}</div>}
      </div>
    </div>
  );
}