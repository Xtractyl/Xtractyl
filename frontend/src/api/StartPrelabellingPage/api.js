// src/api/StartPrelabellingPage/api.js
const OLLAMA_BASE = import.meta.env.VITE_OLLAMA_BASE || "http://localhost:11434";
const ORCH_BASE   = import.meta.env.VITE_ORCH_BASE   || "http://localhost:5001";

// ------------ helpers ------------
function okOrThrow(res, data) {
  if (!res.ok) {
    const msg = (data && (data.error || data.message)) || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

function unwrapLogs(obj) {
  // Orchestrator returns { status, logs: {...} }
  return obj && typeof obj === "object" && obj.logs ? obj.logs : obj;
}

function normalizeStatus(raw) {
  const logs = unwrapLogs(raw) || {};
  // backend stores "progress" often as string "0"…"100"
  let p = logs.progress;
  let frac = 0;
  if (typeof p === "number") {
    // if someone already sends 0..1 or 0..100, handle both
    frac = p > 1 ? Math.min(1, Math.max(0, p / 100)) : Math.min(1, Math.max(0, p));
  } else if (typeof p === "string" && p.trim() !== "") {
    const n = Number(p);
    frac = isFinite(n) ? Math.min(1, Math.max(0, n / 100)) : 0;
  }

  return {
    job_id: logs.job_id,
    state: logs.state,
    progress: frac,
    error: logs.error || "",
    result: logs.result,
    created_at: logs.created_at,
    message: logs.message,
  };
}

// ------------ Ollama ------------
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
        // ignore partial lines
      }
    }
  }
}

export async function listModels(baseUrl = OLLAMA_BASE) {
  const res = await fetch(`${baseUrl}/api/tags`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return Array.isArray(data?.models)
    ? data.models.map((m) => m.model || m.name).filter(Boolean)
    : [];
}

// ------------ Orchestrator ------------
export async function listQalJsons(projectName, base = ORCH_BASE) {
  const url = `${base}/list_qal_jsons?project=${encodeURIComponent(projectName)}`;
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  okOrThrow(res, data);
  return Array.isArray(data) ? data : [];
}

export async function previewQal(projectName, fileName, base = ORCH_BASE) {
  const url = `${base}/preview_qal?project=${encodeURIComponent(projectName)}&file=${encodeURIComponent(fileName)}`;
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  okOrThrow(res, data);
  return data;
}

export async function prelabelProject(payload, base = ORCH_BASE) {
  const url = `${base.replace(/\/$/, "")}/prelabel_project`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  okOrThrow(res, data);
  // return only the logs object so the component can read .job_id directly
  return unwrapLogs(data);
}

export async function cancelPrelabel(preJobId, base = ORCH_BASE) {
  const url = `${base.replace(/\/$/, "")}/prelabel/cancel/${encodeURIComponent(preJobId)}`;
  const res = await fetch(url, { method: "POST" });
  const data = await res.json().catch(() => ({}));
  okOrThrow(res, data);
  return unwrapLogs(data);
}

export async function getPrelabelStatus(jobId, base = ORCH_BASE) {
  const url = `${(base || ORCH_BASE).replace(/\/$/, "")}/prelabel/status/${encodeURIComponent(jobId)}`;
  const res = await fetch(url);
  if (res.status === 404) return { notFound: true };
  const data = await res.json().catch(() => ({}));
  okOrThrow(res, data);
  return normalizeStatus(data);
}