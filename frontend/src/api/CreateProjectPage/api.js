// api/CreateProjectPage/api.js

const ORCH_BASE = import.meta.env.VITE_ORCH_BASE || "http://localhost:5001";

export async function checkProjectExistsAPI(title) {
  const res = await fetch(`${ORCH_BASE}/project_exists`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }), // exakt wie vorher
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to check project existence");
  }

  return res.json(); // { exists: true/false }
}

export async function createProjectAPI({ title, questions, labels, token }) {
    const res = await fetch(`${ORCH_BASE}/create_project`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, questions, labels, token }),
    });
  
    if (!res.ok) {
      const err = await res.text();
      throw new Error(err || "Failed to create project");
    }
  
    return res.json();
  }


