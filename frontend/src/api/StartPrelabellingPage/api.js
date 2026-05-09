// src/api/StartPrelabellingPage/api.js
 import { request } from "../shared/request";
const ORCH_BASE = (import.meta.env.VITE_ORCH_BASE || "http://localhost:5001").replace(/\/$/, "");
const orch = (path, opts) => request(ORCH_BASE, path, opts);

/** Pull a model from Ollama with streaming progress updates */
/** not updated with request pattern due to streaming */
export async function pullModel(model, onProgress) {
  const res = await fetch(`${ORCH_BASE}/ollama/models/pull`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model }),
  });

  if (!res.ok || !res.body) {
    throw new Error(`Pull failed: HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    let streamError = null;
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const obj = JSON.parse(line);
        if (obj.error) {
                 streamError = new Error(obj.error);
                 break;            }
        if (typeof obj.total === "number" && typeof obj.completed === "number" && obj.total > 0) {
          const pct = Math.round((obj.completed / obj.total) * 100);
          onProgress?.(`${pct}%`);
        } else if (obj.status) {
          onProgress?.(obj.status);
        }
      } catch {
        // ignore partial/garbage lines in the stream
      }
    }
    if (streamError) throw streamError;

  }
}

/** List locally available Ollama models */
export async function listModels() {
   const data = await orch(`/ollama/models`);
   return Array.isArray(data?.models) ? data.models : [];
 }

/** List QAL json files for a project */
 export async function listQalJsons(projectName) {
   const data = await orch(`/list_qal_jsons?project=${encodeURIComponent(projectName)}`);
   return Array.isArray(data.files) ? data.files : [];
 }

/** Preview a QAL file */
 export async function previewQal(projectName, fileName) {
   return orch(`/preview_qal?project=${encodeURIComponent(projectName)}&filename=${encodeURIComponent(fileName)}`);
 }

/**
 * Enqueue prelabel job (or start it, depending on backend).
 * Token is sent via Authorization header, not in the payload.
 */
export async function prelabelProject(payload) {
  const { token, ...rest } = payload;
  console.log("prelabelProject rest:", JSON.stringify(rest, null, 2));
  const url = `${ORCH_BASE}/prelabel_project`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify(rest),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data?.message || data?.error || 
      (Array.isArray(data) ? data.map(d => d.msg).join(", ") : null) ||
      `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

/** Ask backend to cancel a running job (best effort). */
export async function cancelPrelabel(jobId) {
  return orch(`/prelabel/cancel/${encodeURIComponent(jobId)}`, { method: "POST" });
}

/**
 * Get job status. Returns the unwrapped status object:
 * { state, progress, project_name, model, created_at, ... }
 * Returns { state: "NOT_FOUND" } if job does not exist.

 */
 export async function getPrelabelStatus(jobId) {
   return orch(`/prelabel/status/${encodeURIComponent(jobId)}`);
 }