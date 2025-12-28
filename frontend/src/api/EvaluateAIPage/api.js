// src/api/EvaluateAIPage/api.js
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";

export async function fetchEvaluationProjects(apiToken) {
  const resp = await fetch(
    `${ORCH_BASE}/evaluate-ai/projects?token=${encodeURIComponent(apiToken)}`
  );

  const data = await resp.json().catch(() => ({}));

  if (!resp.ok || (data.status && data.status !== "success")) {
    const err = new Error(data.error || "Orchestrator request failed");
    err.status = resp.status;
    err.body = data;
    throw err;
  }

  return data.logs || [];
}

export async function evaluateAI(apiToken, groundtruthProject, comparisonProject) {
  const resp = await fetch(`${ORCH_BASE}/evaluate-ai`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      token: apiToken,
      groundtruth_project: groundtruthProject,
      comparison_project: comparisonProject,
    }),
  });

  const data = await resp.json().catch(() => ({}));

  if (!resp.ok || (data.status && data.status !== "success")) {
    const err = new Error(data.error || "Evaluation request failed");
    err.status = resp.status;
    err.body = data;
    throw err;
  }

  return data.logs || data;
}