import React, { useEffect, useState } from "react";
import { fetchEvaluationProjects } from "../../api/EvaluateAIPage/api";

export default function EvaluateAICard({ apiToken }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [selectedProject, setSelectedProject] = useState("");

  // Load project names from orchestrator
  useEffect(() => {
    if (!apiToken) return;

    setLoading(true);
    setErrorMsg("");

    fetchEvaluationProjects(apiToken)
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
  }, [apiToken]);

  return (
    <div className="p-8 bg-[#e6e2cf] min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Evaluate AI</h1>
      <p className="text-gray-600">
        This feature will be included in later releases. It will allow you
        to compare a model against others using metrics like precision,
        recall, and F1.
      </p>

      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-2">Select a project</h2>

        {!apiToken && (
          <p className="text-sm text-red-700">
            Please provide a Label Studio API token.
          </p>
        )}

        {apiToken && (
          <>
            {loading && <p className="text-sm">Loading projects…</p>}

            {errorMsg && (
              <p className="text-sm text-red-600">{errorMsg}</p>
            )}

            {!loading && !errorMsg && (
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

                {selectedProject && (
                  <p className="mt-3 text-sm text-gray-700">
                    Selected: <b>{selectedProject}</b>
                  </p>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}