// src/api/EvaluateAIPage/api.js
import { request } from "../shared/request";
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";
const r = (path, opts) => request(ORCH_BASE, path, opts);

 export async function fetchEvaluationProjects(apiToken) {
   const data = await r(`/evaluate-ai/projects`, {
     headers: { Authorization: `Bearer ${apiToken}` },
   });
   return Array.isArray(data.names) ? data.names : [];
 }

 export async function evaluateAI(apiToken, groundtruthProject, comparisonProject) {
   return r(`/evaluate-ai`, {
     method: "POST",
     headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
     body: JSON.stringify({ groundtruth_project: groundtruthProject, comparison_project: comparisonProject }),
   });
 }

 export async function saveAsGtSet(apiToken, sourceProject, gtSetName) {
   return r(`/save-as-gt-set`, {
     method: "POST",
     headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
     body: JSON.stringify({ source_project: sourceProject, gt_set_name: gtSetName }),
   });
 }