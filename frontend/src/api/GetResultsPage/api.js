// frontend/src/api/getResultsTable.js
import { request } from "../shared/request";
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";
const r = (path, opts) => request(ORCH_BASE, path, opts);

 export async function getProjectsReadyForResults() {
   const data = await r(`/list_projects_ready_for_results`);
   return data.projects;
 }

 export async function getResultsTable({ projectName}) {
   const data = await r(`/results/table`, {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify({ project_name: projectName }),
   });
   return {
     columns: Array.isArray(data.columns) ? data.columns : [],
     rows: Array.isArray(data.rows) ? data.rows : [],
     total: typeof data.total === "number" ? data.total : 0,
   };
 }
