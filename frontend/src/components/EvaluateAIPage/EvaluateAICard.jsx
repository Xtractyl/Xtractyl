import React, { useEffect, useState } from "react";
import { fetchEvaluationProjects } from "../../api/EvaluateAIPage/api";

const LS_BASE = import.meta.env.VITE_LS_BASE || "http://localhost:8080"; //just for the link

export default function EvaluateAICard({ apiToken }) {
  const [localToken, setToken] = useState(apiToken || "");
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [selectedProject, setSelectedProject] = useState("");

  // Load project names from orchestrator
  useEffect(() => {
    if (!localToken) return;

    setLoading(true);
    setErrorMsg("");

    fetchEvaluationProjects(localToken)
      .then((names) => {
        setProjects(names);
        if (names.length > 0) {
          setSelectedProject(names[0]);
        }
      })
      .catch((err) => {
        console.error(err);
        setErrorMsg("Failed to load Label Studio projects.");
      })
      .finally(() => setLoading(false));
  }, [localToken]);

  return (
    <div className="p-8 bg-[#e6e2cf] min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Evaluate AI</h1>

      <p className="text-gray-600">
        Select a groundtruth project, select a prelabelled project on the same tasks to get evaluation metrics.
      </p>

      {/* === TOKEN SECTION (same logic as your other page) === */}
      <div className="mt-8">
        <div>
          <a
            href={`${LS_BASE}/user/account/legacy-token`}
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
              href={`${LS_BASE}/organization/`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#6baa56] hover:underline"
            >
              {LS_BASE}/organization
            </a>{" "}
            and enable it via the API Tokens settings.
          </p>
        </div>

        <div className="mt-3">
          <label className="block text-sm font-medium mb-1">
            Label Studio Token
          </label>

          <input
            type="password"
            value={localToken}
            onChange={(e) => setToken(e.target.value)}
            placeholder={localToken || "Enter your Label Studio token"}
            className="w-full border rounded px-3 py-2"
            autoComplete="off"
            spellCheck={false}
          />
        </div>
      </div>

      {/* === PROJECT SELECTION === */}
      {localToken && (
        <div className="mt-8">
          <h2 className="text-sm font-medium mb-1">Select a groundtruth project</h2>

          {loading && <p className="text-sm">Loading projects…</p>}

          {errorMsg && (
            <p className="text-sm text-red-600">{errorMsg}</p>
          )}

          {!loading && !errorMsg && projects.length > 0 && (
            <>
              <select
                className="w-full p-2 border rounded bg-white mt-2"
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
              >
                {projects.map((name, idx) => (
                  <option key={idx} value={name}>
                    {name}
                  </option>
                ))}
              </select>

              <p className="mt-3 text-sm text-gray-700">
                Selected: <b>{selectedProject}</b>
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}