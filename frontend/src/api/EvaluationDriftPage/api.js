// src/api/EvaluationDriftPage/api.js
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";

export async function fetchEvaluationDrift() {
  const resp = await fetch(`${ORCH_BASE}/evaluation-drift`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  const data = await resp.json().catch(() => ({}));

  if (!resp.ok || (data.status && data.status !== "success")) {
    const err = new Error(data.error || "Drift request failed");
    err.status = resp.status;
    err.body = data;
    throw err;
  }

  // ok() wrapper => {status:"success", data: ...}
  return data.data || data;
}