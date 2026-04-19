// src/components/StartPrelabellingPage/StartPrelabellingCard.jsx
import { useEffect, useState } from "react";
import ModelDownloadInput from "./ModelDownloadInput";
import ProjectNameInput from "../shared/ProjectNameInput";
import ModelPicker from "./ModelPicker";
import SystemPromptInput from "./SystemPromptInput";
import QuestionsAndLabelsPicker from "./QuestionsAndLabelsPicker";
import { prelabelProject, cancelPrelabel, getPrelabelStatus } from "../../api/StartPrelabellingPage/api.js";
import { useAppContext } from "../../context/AppContext";
import TokenLink from "../shared/TokenLink";


const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";
const LS_BASE = import.meta.env.VITE_LS_BASE || "http://localhost:8080"; // only for links

export default function StartPrelabellingCard() {
  const [model, setModel] = useState(() => localStorage.getItem("ollamaModel") || "");
  const [refreshKey, setRefreshKey] = useState(0);
  const [systemPrompt, setSystemPrompt] = useState(
    () => localStorage.getItem("xtractylSystemPrompt") || ""
  );
  const { token, projectName, saveToken, saveProjectName } = useAppContext();
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

  useEffect(() => { try { localStorage.setItem("ollamaModel", model || ""); } catch {} }, [model]);
  useEffect(() => { try { localStorage.setItem("xtractylSystemPrompt", systemPrompt || ""); } catch {} }, [systemPrompt]);
  useEffect(() => { try { localStorage.setItem("xtractylQALFile", qalFile || ""); } catch {} }, [qalFile]);

  const handleQalChange = (_project, file, json) => {
    setQalFile(file);
    setQuestionsAndLabels(json);
  };

const canStart =
    !!projectName && !!model && !!systemPrompt.trim() && !!qalFile && !!token && !preJobId;

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
        questions_and_labels: questionsAndLabels,
      };

      // api.js returns unwrapped { job_id, ... }
      const result = await prelabelProject(payload);
      const jobId = result?.job_id;
      if (jobId) {
        setPreJobId(jobId);
        try { localStorage.setItem("prelabelJobId", jobId); } catch {}
      }

      setStatusMsg("✅ Prelabeling started.");
    } catch (e) {
      setStatusMsg(`❌ ${e?.message || "Failed to start."}`);
    } finally {
      setBusy(false);
    }
  };

  const handleCancel = async () => {
    if (!preJobId) return;
    try {
      await cancelPrelabel(preJobId);
      const s = await getPrelabelStatus(preJobId); // unwrapped
      const st = String(s?.state || "").toUpperCase();

      if (st === "CANCEL_REQUESTED") {
        setStatusMsg("🛑 Cancel requested.");
      } else if (st === "CANCELLED") {
        setStatusMsg("🛑 Cancelled.");
      } else if (st === "SUCCEEDED" || st === "DONE") {
        setStatusMsg("ℹ️ Already finished.");
      } else if (st === "FAILED" || st === "ERROR") {
        setStatusMsg("⚠️ Job failed.");
      } else {
        setStatusMsg(`ℹ️ State: ${st || "unknown"}`);
      }
    } catch (e) {
      setStatusMsg(`❌ ${e?.message || "Cancel failed."}`);
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
        const s = await getPrelabelStatus(preJobId); // unwrapped
        if (s?.notFound) {
          localStorage.removeItem("prelabelJobId");
          setPreJobId("");
          setPreStatus(null);
          return;
        }

        setPreStatus(s);

        const st = String(s?.state || "").toLowerCase();
        const pct = Number(s?.progress ?? 0);

        // terminal states
        if (["done", "error", "failed", "cancelled", "succeeded"].includes(st)) {
          localStorage.removeItem("prelabelJobId");
          setPreJobId("");
          return;
        }

        // special-case cancel requested at 100% (worker may have stopped after last step)
        if (st === "cancel_requested" && pct >= 100) {
          localStorage.removeItem("prelabelJobId");
          setPreJobId("");
          setStatusMsg("✅ Job finished (cancel request acknowledged).");
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

  const progressPct = Math.round(Number(preStatus?.progress ?? 0));

  return (
    <div className="p-6 bg-xtractyl-background min-h-screen text-xtractyl-darktext">
      <h1 className="text-2xl font-semibold mb-4">Start AI</h1>
      <p className="text-xtractyl-outline/70 mb-6">
        Download a model (if needed), enter your project, pick an installed model, set a system prompt, choose your Questions & Labels JSON, then start prelabeling.
      </p>

      <div className="mb-6">
        <ModelDownloadInput onDone={() => setRefreshKey((k) => k + 1)} />
      </div>

      <div className="space-y-6 bg-xtractyl-offwhite p-6 rounded shadow max-w-3xl">
      <ProjectNameInput value={projectName} onChange={saveProjectName} />
        <div className="text-sm text-xtractyl-outline/70 -mt-2">
          <div>Forgot your project name?</div>
          <a
            href="http://localhost:8080/projects/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block text-xtractyl-green hover:underline"
          >
            Open Label Studio projects
          </a>
        </div>

        <div>
          < TokenLink />
        </div>

        <div className="mt-3">
          <label className="block text-sm font-medium mb-1">Label Studio Token</label>
          <input
            type="password"
            value={token}
            onChange={(e) => saveToken(e.target.value)}
            placeholder={token || "Enter your Label Studio token"}
            className="w-full border rounded px-3 py-2"
            autoComplete="off"
            spellCheck={false}
          />
        </div>

        <ModelPicker selectedModel={model} onChange={setModel} refreshKey={refreshKey} />

        <SystemPromptInput
          value={systemPrompt}
          onChange={setSystemPrompt}
          persistKey="xtractylSystemPrompt"
        />

        <QuestionsAndLabelsPicker
          projectName={projectName}
          selectedFile={qalFile}
          onChange={handleQalChange}
        />

        <div className="pt-2 text-sm text-xtractyl-outline/70">
          <div>
            Project: <span className="font-mono">{projectName || "—"}</span>
          </div>
          <div>
            Model: <span className="font-mono">{model || "—"}</span>
          </div>
          <div>
            Q&L JSON: <span className="font-mono">{qalFile || "—"}</span>
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="button"
            onClick={handleStart}
            disabled={!canStart || busy}
            className={`px-4 py-2 rounded text-xtractyl-white ${
              !canStart || busy ? "bg-xtractyl-green/50 cursor-not-allowed" : "bg-xtractyl-green hover:bg-xtractyl-green/80 transition"
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
                ? "bg-xtractyl-orange text-xtractyl-white hover:bg-xtractyl-orange/80 transition"
                : "bg-xtractyl-offwhite text-xtractyl-outline cursor-not-allowed"
            }`}
          >
            Cancel
          </button>
        </div>

        {(preJobId || preStatus) && (
          <div className="mt-4 bg-xtractyl-offwhite p-4 rounded">
            <div className="font-medium mb-1">
              Status: {preStatus?.state || "queued"}{" "}
              {Number.isFinite(progressPct) ? `— ${progressPct}%` : ""}
            </div>
            <div className="w-full h-2 bg-xtractyl-offwhite rounded">
              <div
                className="h-2 bg-xtractyl-green rounded"
                style={{ width: `${Number.isFinite(progressPct) ? progressPct : 0}%` }}
              />
            </div>
            {preStatus?.message && <div className="text-sm mt-2">{preStatus.message}</div>}
            {preJobId && (
              <div className="text-xs text-xtractyl-outline/70 mt-1">
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