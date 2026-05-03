// src/api/UploadTasksPage/api.js
import { request } from "../shared/request";
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";
const r = (path, opts) => request(ORCH_BASE, path, opts);

/** POST /upload_tasks -> { ...result } */
 export async function uploadTasks({ projectName, token, htmlFolder }) {
   return r(`/upload_tasks`, {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify({ project: projectName, token, html_folder: htmlFolder }),
   });
 }

 export async function getHtmlSubfolders() {
   const data = await r(`/list_html_subfolders`);
   return data.subfolders;
 }
