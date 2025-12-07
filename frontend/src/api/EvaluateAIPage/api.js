// src/api/EvaluateAIPage/api.js
// API functions for the Evaluate AI page:
// - Fetch available projects for evaluation
// - Execute the evaluation via orchestrator

const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";

/**
 * Fetch project names from orchestrator
 * The orchestrator communicates with Label Studio on behalf of the client.
 */
export async function fetchEvaluationProjects(apiToken) {
  const resp = await fetch(
    `${ORCH_BASE}/evaluate-ai/projects?token=${encodeURIComponent(apiToken)}`
  );

  if (!resp.ok) {
    throw new Error("Orchestrator request failed");
  }

  const data = await resp.json();

  if (data.status !== "success") {
    throw new Error(data.error || "Unknown orchestrator error");
  }

  return data.logs || [];
}

/**
 * Execute evaluation for the given groundtruth & comparison project
 */
export async function evaluateAI(apiToken, groundtruthProject, comparisonProject) {
  const resp = await fetch(`${ORCH_BASE}/evaluate-ai`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      token: apiToken,
      groundtruth_project: groundtruthProject,
      comparison_project: comparisonProject,
    }),
  });

  if (!resp.ok) {
    throw new Error("Evaluation request failed");
  }

  const data = await resp.json();

  if (data.status !== "success") {
    throw new Error(data.error || "Unknown evaluation error");
  }

  // Return complete evaluation payload
  return data.result;
}