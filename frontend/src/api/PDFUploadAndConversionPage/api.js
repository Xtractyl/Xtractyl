// api/UploadAndConversionPage/api.js
const DOC_BASE = "http://localhost:5004";

/** kleiner Fetch-Wrapper mit Timeout & konsistentem Error-Objekt */
async function request(path, { method = "GET", headers, body, timeoutMs = 15000 } = {}) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);

  try {
    const res = await fetch(`${DOC_BASE}${path}`, { method, headers, body, signal: ctrl.signal });

    // 204: kein Body, aber ok
    if (res.status === 204) return null;

    const isJson = res.headers.get("content-type")?.includes("application/json");
    const data = isJson ? await res.json().catch(() => ({})) : await res.text();

    if (!res.ok) {
      const msg = (isJson && data?.error) || data?.message || `HTTP ${res.status}`;
      const err = new Error(msg);
      err.status = res.status;
      err.data = data;
      throw err;
    }

    return data;
  } catch (err) {
    if (err.name === "AbortError") {
      const e = new Error("Request timeout");
      e.status = 0;
      throw e;
    }
    throw err;
  } finally {
    clearTimeout(t);
  }
}

/** GET /list-subfolders -> string[] */
export async function listSubfolders() {
  return request(`/list-subfolders`);
}

/** GET /list-files?folder=... -> string[] */
export async function listFiles(folder) {
  const q = encodeURIComponent(folder || "");
  return request(`/list-files?folder=${q}`);
}

/** POST /uploadpdfs (FormData) -> { job_id, message? } | 202 */
export async function uploadPdfs(files, folder) {
  const fd = new FormData();
  fd.append("folder", folder);
  for (const f of files) fd.append("files", f);

  // Server antwortet idealerweise 202 + JSON
  const res = await request(`/uploadpdfs`, { method: "POST", body: fd });
  // Falls Backend mal kein JSON liefert, res wäre string – minimal absichern:
  if (res && typeof res === "object" && "job_id" in res) return res;
  return res; // oder wirfen, je nach Backend-Vertrag
}

/** GET /job_status/:id -> { state, progress?, message?, done?, total? } */
export async function getJobStatus(jobId) {
  return request(`/job_status/${encodeURIComponent(jobId)}`);
}

/** POST /cancel_job/:id -> { status: "cancel_requested" | "already_finished" | "ok", state? } */
export async function cancelJob(jobId) {
  return request(`/cancel_job/${encodeURIComponent(jobId)}`, { method: "POST" });
}

// Optional export, falls du die Base-URL an anderer Stelle brauchst
export { DOC_BASE };