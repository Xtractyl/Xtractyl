// src/components/StartPrelabellingPage/StartPrelabellingCard.jsx
import { useState } from "react";
import ModelDownloadInput from "./ModelDownloadInput";
import ProjectNameInput from "../shared/ProjectNameInput";
import ModelPicker from "./ModelPicker";
import SystemPromptInput from "./SystemPromptInput";
import QuestionsAndLabelsPicker from "./QuestionsAndLabelsPicker";
import TokenLink from "../shared/TokenLink";
import { useAppContext } from "../../context/AppContext";
import { usePrelabelConfig } from "../../hooks/StartPrelabellingPage/usePrelabelConfig";
import { usePrelabelJob } from "../../hooks/StartPrelabellingPage/usePrelabelJob";

export default function StartPrelabellingCard() {
  const [refreshKey, setRefreshKey] = useState(0);
  const { token, projectName, saveToken, saveProjectName } = useAppContext();
  const config = usePrelabelConfig();
  const job = usePrelabelJob();

  const canStart =
    !!projectName && !!config.model && !!config.systemPrompt.trim() &&
    !!config.qalFile && !!token && !job.preJobId;

  const handleStart = () => {
    if (!canStart) return;
    job.start({
      project_name: projectName,
      model: config.model,
      system_prompt: config.systemPrompt,
      qal_file: config.qalFile,
      token,
      questions_and_labels: config.questionsAndLabels,
    });
  };

  return (
    <div className="p-6 bg-xtractyl-background min-h-screen text-xtractyl-darktext">
      <h1 className="text-2xl font-semibold mb-4">Start AI</h1>
      <p className="text-xtractyl-outline/70 mb-6">
        Download a model (if needed), enter your project, pick an installed model,
        set a system prompt, choose your Questions & Labels JSON, then start prelabeling.
      </p>

      <div className="mb-6">
        <ModelDownloadInput onDone={() => setRefreshKey((k) => k + 1)} />
      </div>

      <div className="space-y-6 bg-xtractyl-offwhite p-6 rounded shadow max-w-3xl">
        <ProjectNameInput value={projectName} onChange={saveProjectName} />
        <div className="text-sm text-xtractyl-outline/70 -mt-2">
          <div>Forgot your project name?</div>
          <a href="http://localhost:8080/projects/" target="_blank" rel="noopener noreferrer"
            className="inline-block text-xtractyl-green hover:underline">
            Open Label Studio projects
          </a>
        </div>

        <div><TokenLink /></div>
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

        <ModelPicker selectedModel={config.model} onChange={config.setModel} refreshKey={refreshKey} />
        <SystemPromptInput value={config.systemPrompt} onChange={config.setSystemPrompt} />
        <QuestionsAndLabelsPicker projectName={projectName} selectedFile={config.qalFile} onChange={config.handleQalChange} />

        <div className="pt-2 text-sm text-xtractyl-outline/70">
          <div>Project: <span className="font-mono">{projectName || "—"}</span></div>
          <div>Model: <span className="font-mono">{config.model || "—"}</span></div>
          <div>Q&L JSON: <span className="font-mono">{config.qalFile || "—"}</span></div>
        </div>

        <div className="flex gap-3 pt-2">
          <button type="button" onClick={handleStart} disabled={!canStart || job.busy}
            className={`px-4 py-2 rounded text-xtractyl-white ${!canStart || job.busy ? "bg-xtractyl-green/50 cursor-not-allowed" : "bg-xtractyl-green hover:bg-xtractyl-green/80 transition"}`}>
            {job.busy ? "Starting…" : "Start Prelabeling"}
          </button>
          <button type="button" onClick={job.cancel} disabled={!job.preJobId}
            className={`px-4 py-2 rounded ${job.preJobId ? "bg-xtractyl-orange text-xtractyl-white hover:bg-xtractyl-orange/80 transition" : "bg-xtractyl-offwhite text-xtractyl-outline cursor-not-allowed"}`}>
            Cancel
          </button>
        </div>

        {(job.preJobId || job.preStatus) && (
          <div className="mt-4 bg-xtractyl-offwhite p-4 rounded">
            <div className="font-medium mb-1">
              Status: {job.preStatus?.state || "queued"}{" "}
              {Number.isFinite(job.progressPct) ? `— ${job.progressPct}%` : ""}
            </div>
            <div className="w-full h-2 bg-xtractyl-offwhite rounded">
              <div className="h-2 bg-xtractyl-green rounded"
                style={{ width: `${Number.isFinite(job.progressPct) ? job.progressPct : 0}%` }} />
            </div>
            {job.preStatus?.message && <div className="text-sm mt-2">{job.preStatus.message}</div>}
            {job.preJobId && (
              <div className="text-xs text-xtractyl-outline/70 mt-1">
                Job ID: <span className="break-all">{job.preJobId}</span>
              </div>
            )}
          </div>
        )}

        {job.statusMsg && <div className="text-sm mt-2">{job.statusMsg}</div>}
      </div>
    </div>
  );
}