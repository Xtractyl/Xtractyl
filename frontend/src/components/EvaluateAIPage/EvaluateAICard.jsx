// src/components/EvaluateAIPage/EvaluateAICard.jsx
import React, { useEffect, useState } from "react";
import { fetchEvaluationProjects, evaluateAI } from "../../api/EvaluateAIPage/api.js";
import ComparisonSelection from "./ComparisonSelection.jsx";
import EvaluationResults from "./EvaluationResults.jsx";

const LS_BASE = import.meta.env.VITE_LS_BASE || "http://localhost:8080"; // just for the link

export default function EvaluateAICard({ apiToken }) {
  const [localToken, setToken] = useState(apiToken || "");
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [groundtruthProject, setGroundtruthProject] = useState("");
  const [comparisonProject, setComparisonProject] = useState("");
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalError, setEvalError] = useState("");
  const [evalResult, setEvalResult] = useState(null);

  // Load project names from orchestrator
  useEffect(() => {
    if (!localToken) return;

    setLoading(true);
    setErrorMsg("");

    fetchEvaluationProjects(localToken)
      .then((names) => {
        setProjects(names || []);
        if (names && names.length > 0) {
          // Default beide auf das erste Projekt setzen
          setGroundtruthProject((prev) => prev || names[0]);
          setComparisonProject((prev) => prev || names[0]);
        } else {
          setGroundtruthProject("");
          setComparisonProject("");
        }
      })
      .catch((err) => {
        console.error(err);
        setErrorMsg("Failed to load Label Studio projects.");
        setProjects([]);
        setGroundtruthProject("");
        setComparisonProject("");
      })
      .finally(() => setLoading(false));
  }, [localToken]);

  const handleRunEvaluation = async () => {
    setEvalLoading(true);
    setEvalError("");
    setEvalResult(null);

    try {
      const result = await evaluateAI(
        localToken,
        groundtruthProject,
        comparisonProject
      );

      setEvalResult(result);
    } catch (err) {
      console.error(err);
      setEvalError("Evaluation failed. Please try again.");
    } finally {
      setEvalLoading(false);
    }
  };

  return (
    <div className="p-8 bg-[#e6e2cf] min-h-screen text-[#23211c]">
      <h1 className="text-2xl font-semibold mb-4">Evaluate AI</h1>

      <p className="text-gray-600">
        Select a groundtruth project and a prelabelled project on the same tasks
        to get evaluation metrics.
      </p>

      {/* === TOKEN SECTION === */}
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

      {/* === COMPARISON SELECTION === */}
      {localToken && (
        <ComparisonSelection
          projects={projects}
          loading={loading}
          errorMsg={errorMsg}
          groundtruthProject={groundtruthProject}
          setGroundtruthProject={setGroundtruthProject}
          comparisonProject={comparisonProject}
          setComparisonProject={setComparisonProject}
          onSubmit={handleRunEvaluation}
        />
      )}

      {/* === EVALUATION RESULTS === */}
      {localToken && (
        <EvaluationResults
          loading={evalLoading}
          errorMsg={evalError}
          result={evalResult}
        />
      )}
    </div>
  );
}