// src/api/StartPrelabellingPage/api.js

const OLLAMA_BASE = import.meta.env.VITE_OLLAMA_BASE || "http://localhost:11434";
const ORCH_BASE = (import.meta.env.VITE_ORCH_BASE || "http://localhost:5001").replace(/\/$/, "");

/** Pull a model from Ollama with streaming progress updates */
export async function pullModel(model, onProgress, baseUrl = OLLAMA_BASE) {
  const res = await fetch(`${baseUrl}/api/pull`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: model }),
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

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const obj = JSON.parse(line);
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
  }
}

/** List locally available Ollama models */
export async function listModels(baseUrl = OLLAMA_BASE) {
  const res = await fetch(`${baseUrl}/api/tags`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();

  return Array.isArray(data?.models)
    ? data.models.map((m) => m.model || m.name).filter(Boolean)
    : [];
}

/** List QAL json files for a project */
export async function listQalJsons(projectName, base = ORCH_BASE) {
  const url = `${base}/list_qal_jsons?project=${encodeURIComponent(projectName)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

/** Preview a QAL file */
export async function previewQal(projectName, fileName, base = ORCH_BASE) {
  const url = `${base}/preview_qal?project=${encodeURIComponent(projectName)}&file=${encodeURIComponent(fileName)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/**
 * Enqueue prelabel job (or start it, depending on backend).
 * Returns the unwrapped payload so callers can read job_id directly.
 */
export async function prelabelProject(payload, base = ORCH_BASE) {
  const url = `${base}/prelabel_project`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);

  // Orchestrator wraps under { status, logs: {...} }
  return data?.logs ?? data;
}

/** Ask backend to cancel a running job (best effort). */
export async function cancelPrelabel(jobId, base = ORCH_BASE) {
  const url = `${base}/prelabel/cancel/${encodeURIComponent(jobId)}`;
  const res = await fetch(url, { method: "POST" });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);
  return data?.logs ?? data;
}

/**
 * Get job status. Returns the unwrapped status object:
 * { state, progress, project_name, model, created_at, ... }
 * If not found: { notFound: true }
 */
export async function getPrelabelStatus(jobId, base = ORCH_BASE) {
  const url = `${base}/prelabel/status/${encodeURIComponent(jobId)}`;
  const res = await fetch(url);

  if (res.status === 404) {
    return { notFound: true };
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);

  return data?.logs ?? data;
}