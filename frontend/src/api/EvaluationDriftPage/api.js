// src/api/EvaluationDriftPage/api.js
 import { request } from "../shared/request";
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";
const r = (path, opts) => request(ORCH_BASE, path, opts);

export async function fetchEvaluatedProjects() {
  const data = await r(`/evaluations/projects`);
  return data.projects || [];
}

export async function fetchComparisonView(projectName) {
  const params = new URLSearchParams({ project_name: projectName });
  return await r(`/evaluations/comparison?${params}`);
}

export async function fetchRegressionView(projectName) {
  const params = new URLSearchParams({ project_name: projectName });
  return await r(`/evaluations/regression?${params}`);
}

export async function fetchDriftView(projectName) {
  const params = new URLSearchParams({ project_name: projectName });
  return await r(`/evaluations/drift?${params}`);
}