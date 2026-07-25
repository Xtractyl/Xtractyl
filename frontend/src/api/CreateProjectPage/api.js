// api/CreateProjectPage/api.js
import { request } from "../shared/request";
const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";
const r = (path, opts) => request(ORCH_BASE, path, opts);

 export async function createProjectAPI({ title, questions, labels, token }) {
   return r(`/create_project`, {
     method: "POST",
     headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
     body: JSON.stringify({ title, questions, labels }),
   });
 }

 export async function fetchGroundtruthQuestionsAndLabels() {
   const data = await r(`/groundtruth_qals`);
   return data.sets;
 }

 export async function getProjectsWithoutLabelStudioId() {
   const data = await r(`/list_projects_without_label_studio_id`);
  return data.projects;
}