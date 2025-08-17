// api/createProject.js
export async function createProjectAPI({ title, questions, labels, token }) {
    const res = await fetch("http://localhost:5001/create_project", {
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