const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";

/**
 * Fetch project names from orchestrator (not Label Studio directly)
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