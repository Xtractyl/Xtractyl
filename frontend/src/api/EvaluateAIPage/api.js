// src/api/EvaluateAIPage/api.js
import { request } from "../shared/request";
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";
const r = (path, opts) => request(ORCH_BASE, path, opts);

 export async function getProjectsReadyForGroundtruth() {
   const data = await r(`/list_projects_ready_for_groundtruth`);
   return Array.isArray(data.projects) ? data.projects : [];
 }

 export async function saveAsGtSet(apiToken, sourceProject, scope) {
   return r(`/save-as-gt-set`, {
     method: "POST",
     headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
     body: JSON.stringify({ source_project: sourceProject, scope }),
   });
 }

 export async function getProjectsReadyForComparison() {
   const data = await r(`/list_projects_ready_for_comparison`);
   return Array.isArray(data.projects) ? data.projects : [];
 }

  export async function getGroundtruthProjectsForComparison(comparisonProject) {
   const data = await r(`/list_groundtruth_projects_for_comparison`, {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify({ comparison_project: comparisonProject }),
   });
   return Array.isArray(data.projects) ? data.projects : [];
 }

 export async function evaluateAI(apiToken, groundtruthProject, comparisonProject) {
   return r(`/evaluate-ai`, {
     method: "POST",
     headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
     body: JSON.stringify({ groundtruth_project: groundtruthProject, comparison_project: comparisonProject }),
   });
 }

