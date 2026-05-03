// src/api/EvaluationDriftPage/api.js
 import { request } from "../shared/request";
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";
const r = (path, opts) => request(ORCH_BASE, path, opts);

 export async function fetchEvaluationDrift() {
   const data = await r(`/evaluation-drift`);
   return data.data || data;
 }