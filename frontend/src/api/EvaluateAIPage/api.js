// src/api/EvaluateAIPage/api.js
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";

export async function fetchEvaluationProjects(apiToken) {
  const resp = await fetch(`${ORCH_BASE}/evaluate-ai/projects`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${apiToken}`,
    },
  });

  const data = await resp.json().catch(() => ({}));

  if (!resp.ok)  {
    const err = new Error(data.error || "Orchestrator request failed");
    err.status = resp.status;
    err.body = data;
    throw err;
  }

  return Array.isArray(data.names) ? data.names : [];
}

export async function evaluateAI(apiToken, groundtruthProject, comparisonProject) {
  const resp = await fetch(`${ORCH_BASE}/evaluate-ai`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiToken}`,
    },
    body: JSON.stringify({
      groundtruth_project: groundtruthProject,
      comparison_project: comparisonProject,
    }),
  });

  const data = await resp.json().catch(() => ({}));

  if (!resp.ok) {
    const err = new Error(data.error || "Evaluation request failed");
    err.status = resp.status;
    err.body = data;
    throw err;
  }

  return data;
}


export async function saveAsGtSet(apiToken, sourceProject, gtSetName) {
  const resp = await fetch(`${ORCH_BASE}/save-as-gt-set`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiToken}`,
    },
    body: JSON.stringify({
      source_project: sourceProject,
      gt_set_name: gtSetName,
    }),
  });

  const data = await resp.json().catch(() => ({}));

  if (!resp.ok) {
    const err = new Error(data.error || "Save as GT set failed");
    err.status = resp.status;
    err.body = data;
    throw err;
  }

  return data;
}