// api/CreateProjectPage/api.js
import { request } from "../shared/request.js";
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";
const r = (path, opts) => request(ORCH_BASE, path, opts);

export async function createProject({ title, questions, labels, token }) {
  return r(`/create-project`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ title, questions, labels }),
  });
}

export async function fetchGroundtruthQuestionsAndLabels() {
  const data = await r(`/groundtruth-qals`);
  return data.sets;
}

export async function getProjectsReadyForCreation() {
  const data = await r(`/list-projects-ready-for-creation`);
  return data.projects;
}

export async function getProjectLinks({ title, questions, labels }) {
  return r(`/project-links`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, questions, labels }),
  });
}

export async function discardProject(project) {
  return r(`/discard-project`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project }),
  });
}
