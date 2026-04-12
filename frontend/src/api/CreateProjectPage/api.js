// api/CreateProjectPage/api.js

const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";

export async function checkProjectExistsAPI(project) {
  const res = await fetch(`${ORCH_BASE}/project_exists`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project }), 
  });

  if (res.status === 409) {
    throw new Error("PROJECT_ALREADY_EXISTS");
  }
  if (!res.ok) {
    throw new Error("Failed to check project existence");
  }
  return res.json();
}

export async function createProjectAPI({ title, questions, labels, token }) {
    const res = await fetch(`${ORCH_BASE}/create_project`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({ title, questions, labels }),
    });
  
    if (!res.ok) {
      const err = await res.text();
      throw new Error(err || "Failed to create project");
    }
  
    return res.json();
  }

export async function fetchGroundtruthQuestionsAndLabels() {
  const resp = await fetch(`${ORCH_BASE}/groundtruth_qals`);
  const data = await resp.json();
  if (!resp.ok) {
    throw new Error(`Failed to fetch groundtruth Q&L (${resp.status})`);
  }
  return data.sets;
}