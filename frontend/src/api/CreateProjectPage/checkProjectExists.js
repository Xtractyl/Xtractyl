// api/checkProjectExists.js
const ORCH_BASE = "http://localhost:5001";

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