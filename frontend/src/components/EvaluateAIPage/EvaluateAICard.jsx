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
        const SPECIAL = "Evaluation_Set_Do_Not_Delete";
        const projectList = names || [];

        const hasSpecial = projectList.includes(SPECIAL);

        // Groundtruth-Projekte: SPECIAL genau einmal drin
        const groundtruthOptions = hasSpecial
          ? projectList
          : [SPECIAL, ...projectList];

        setProjects(groundtruthOptions);

        // Defaults setzen
        // Groundtruth: SPECIAL wenn möglich, sonst erstes Groundtruth-Projekt
        if (groundtruthOptions.length > 0) {
          const defaultGT = groundtruthOptions.includes(SPECIAL)
            ? SPECIAL
            : groundtruthOptions[0];
          setGroundtruthProject((prev) => prev || defaultGT);
        } else {
          setGroundtruthProject("");
        }

        // Comparison: erstes Projekt, das NICHT SPECIAL ist
        const comparisonCandidates = groundtruthOptions.filter(
          (name) => name !== SPECIAL
        );

        if (comparisonCandidates.length > 0) {
          setComparisonProject(
            (prev) => prev || comparisonCandidates[0]
          );
        } else {
          setComparisonProject("");
        }
      })
      .catch((err) => {
        setErrorMsg("Failed to load Label Studio projects.");
        const SPECIAL = "Evaluation_Set_Do_Not_Delete";
        // Fallback: nur Groundtruth mit SPECIAL, Comparison leer
        setProjects([SPECIAL]);
        setGroundtruthProject(SPECIAL);
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
    } catch {
      setEvalError("Evaluation failed.");
    } finally {
      setEvalLoading(false);
    }
  };

  return (
    <div className="p-8 bg-xtractyl-background min-h-screen text-xtractyl-darktext">
      <h1 className="text-2xl font-semibold mb-4">Evaluate AI</h1>

      <p className="text-xtractyl-outline/70">
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
            className="inline-block bg-xtractyl-orange text-xtractyl-white font-medium px-5 py-2 rounded shadow hover:bg-xtractyl-orange/80 transition"
          >
            Get your legacy token
          </a>

          <p className="mt-2 text-sm text-xtractyl-outline/60">
            Return here after copying the token from Label Studio.
          </p>

          <p className="mt-1 text-sm text-xtractyl-outline/60">
            ⚠️ If you see no legacy token there, go to{" "}
            <a
              href={`${LS_BASE}/organization/`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xtractyl-green hover:underline"
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
            className="w-full border border-xtractyl-outline/30 rounded px-3 py-2 bg-xtractyl-white text-xtractyl-darktext"
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