import { useState } from "react";
import TokenInput from "./TokenInput";
import CreateProjectForm from "./CreateProjectForm";

const ORCH_BASE = "http://localhost:5001"; // Orchestrator (backend)
const LS_BASE   = "http://localhost:8080"; // Label Studio

export default function CreateProjectCard({ onTokenSave }) {
  const [apiToken, setApiToken] = useState(() => localStorage.getItem("lsToken") || "");

  const handleLocalTokenSave = (token) => {
    setApiToken(token);
    try { localStorage.setItem("lsToken", token); } catch {}
    if (onTokenSave) onTokenSave(token);
  };

  const handleFormSubmit = async (formData) => {
    const payload = {
      title: formData.title,
      questions: formData.questions,
      labels: formData.labels,
      token: apiToken,
    };

    try {
      // Check if project exists
      const checkResponse = await fetch(`${ORCH_BASE}/project_exists`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: formData.title }),
      });
      if (!checkResponse.ok) throw new Error("Failed to check if project exists");

      const checkResult = await checkResponse.json();
      if (checkResult.exists) {
        alert("❌ A project with this name already exists. Please choose a different name.");
        return;
      }

      // Create project
      const response = await fetch(`${ORCH_BASE}/create_project`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

      const result = await response.json();
      console.log("✅ Project created:", result);
      alert("✅ Project successfully created!");
    } catch (error) {
      console.error("❌ Error:", error);
      alert("Something went wrong. See console for details.");
    }
  };

  return (
    <div className="p-8 bg-[#e6e2cf] min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Create Project</h1>
      <p className="text-gray-600 mb-6">Create your project in Label Studio.</p>

      <div className="space-y-6 bg-[#ede6d6] p-8 rounded shadow w-full">
        {/* Token helper */}
        <div>
          <a
            href={`${LS_BASE}/user/account`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-[#db7127] text-white text-base font-medium px-5 py-2 rounded shadow hover:bg-orange-600 transition"
          >
            Get your legacy token
          </a>
          <p className="mt-2 text-sm text-gray-500">
            Return here after copying the token from Label Studio.
          </p>
          <p className="mt-1 text-sm text-gray-500">
            ⚠️ If you see no legacy token there, go to{" "}
            <a
              href={`${LS_BASE}/organization`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#6baa56] hover:underline"
            >
              {LS_BASE}/organization
            </a>{" "}
            and enable it via the API Tokens settings.
          </p>
        </div>

        {/* Token input */}
        <TokenInput onTokenSave={handleLocalTokenSave} />

        {apiToken && (
          <div>
            <p className="text-gray-600 mb-2">Token saved!</p>
            <CreateProjectForm onSubmit={handleFormSubmit} />
          </div>
        )}
      </div>
    </div>
  );
}