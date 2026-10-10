// src/components/StartPrelabellingPage/StartPrelabellingCard.jsx
import { useState } from "react";
import ModelDownloadInput from "./ModelDownloadInput";
import PrelabellingReadyProjectSelect from "./PrelabellingReadyProjectSelect";
import ModelPicker from "./ModelPicker";
import SystemPromptInput from "./SystemPromptInput";
import TokenInput from "../shared/TokenInput";
import { useAppContext } from "../../context/AppContext";
import { usePrelabelConfig } from "../../hooks/StartPrelabellingPage/usePrelabelConfig";
import { usePrelabelJob } from "../../hooks/StartPrelabellingPage/usePrelabelJob";

export default function StartPrelabellingCard() {
  const [refreshKey, setRefreshKey] = useState(0);
  const { token, projectName, saveProjectName } = useAppContext();
  const config = usePrelabelConfig();
  const job = usePrelabelJob();

  const canStart =
    !!projectName && !!config.model && !!config.systemPrompt.trim() && !!token && !job.preJobId;

  const handleStart = () => {
    if (!canStart) return;
    job.start({
      project_name: projectName,
      model: config.model,
      system_prompt: config.systemPrompt,
      token,
    });
  };

  return (
    <div className="p-6 bg-xtractyl-background min-h-screen text-xtractyl-darktext">
      <h1 className="text-2xl font-semibold mb-4">Start AI</h1>
      <p className="text-xtractyl-outline/70 mb-6">
        Download a model (if needed), enter your project, pick an installed model, set a system
        prompt, then start prelabeling.
      </p>

      <div className="space-y-6">
        <div className="mb-6">
          <ModelDownloadInput onDone={() => setRefreshKey((k) => k + 1)} />
        </div>

        <div className="space-y-6 bg-xtractyl-offwhite p-6 rounded shadow">
          <PrelabellingReadyProjectSelect selected={projectName} onChange={saveProjectName} />

          <TokenInput />

          <ModelPicker
            selectedModel={config.model}
            onChange={config.setModel}
            refreshKey={refreshKey}
          />
          <SystemPromptInput value={config.systemPrompt} onChange={config.setSystemPrompt} />

          <div className="pt-2 text-sm text-xtractyl-outline/70">
            <div>
              Project: <span className="font-mono">{projectName || "—"}</span>
            </div>
            <div>
              Model: <span className="font-mono">{config.model || "—"}</span>
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={handleStart}
              disabled={!canStart || job.busy}
              className={`px-4 py-2 rounded text-xtractyl-white ${!canStart || job.busy ? "bg-xtractyl-green/50 cursor-not-allowed" : "bg-xtractyl-green hover:bg-xtractyl-green/80 transition"}`}
            >
              {job.busy ? "Starting…" : "Start Prelabeling"}
            </button>
            <button
              type="button"
              onClick={job.cancel}
              disabled={!job.preJobId}
              className={`px-4 py-2 rounded ${job.preJobId ? "bg-xtractyl-orange text-xtractyl-white hover:bg-xtractyl-orange/80 transition" : "bg-xtractyl-offwhite text-xtractyl-outline cursor-not-allowed"}`}
            >
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
                <div
                  className="h-2 bg-xtractyl-green rounded"
                  style={{ width: `${Number.isFinite(job.progressPct) ? job.progressPct : 0}%` }}
                />
              </div>
              {job.preStatus?.message && (
                <div className="text-sm mt-2">{job.preStatus.message}</div>
              )}
              {job.preJobId && (
                <div className="text-xs text-xtractyl-outline/70 mt-1">
                  Job ID: <span className="break-all">{job.preJobId}</span>
                </div>
              )}
            </div>
          )}
          {/* the following formatting is highly important on resume of a priorily failed
          prelabelling run. The user will get an info through job.statusMsg about the original prompt
          when she/he accidentally used a different prompt now. She/he can only copy it and have it 
          resolve to the original hash, when no additional line breaks etc. are introduced
          ADD explicit unit test later!
          */}
          {job.statusMsg && (
            <div className="text-sm mt-2 whitespace-pre-wrap break-words">{job.statusMsg}</div>
          )}
        </div>
      </div>
    </div>
  );
}
