// src/components/EvaluateAIPage/EvaluateAICard.jsx
import { useEffect, useState } from "react";
import { getProjectsReadyForComparison, getGroundtruthProjectsForComparison, evaluateAI } from "../../api/EvaluateAIPage/api.js";
import { fetchGroundtruthQuestionsAndLabels } from "../../api/CreateProjectPage/api.js";
import SaveAsGtSet from "./SaveAsGtSet.jsx";
import ComparisonSelection from "./ComparisonSelection.jsx";
import EvaluationResults from "./EvaluationResults.jsx";
import { useAppContext } from "../../context/AppContext";
import TokenLink from "../shared/TokenLink";

export default function EvaluateAICard() {
  const {token, saveToken } = useAppContext();
  const [gtSets, setGtSets] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [groundtruthProject, setGroundtruthProject] = useState("");
  const [comparisonProject, setComparisonProject] = useState("");
  const [compatibleGtSets, setCompatibleGtSets] = useState([]);
  const [compatibleLoading, setCompatibleLoading] = useState(false);
  const [compatibleError, setCompatibleError] = useState("");
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalError, setEvalError] = useState("");
  const [evalResult, setEvalResult] = useState(null);
  const [gtSetVersion, setGtSetVersion] = useState(0);

  // Load GT sets from filesystem (independent of token)
  useEffect(() => {
    fetchGroundtruthQuestionsAndLabels()
      .then((sets) => setGtSets(Object.keys(sets || {})))
     .catch((e) => setErrorMsg(e.message || "Failed to load ground truth sets."));
  }, [gtSetVersion]);

  // Load comparison-ready project names from Postgres — no Label Studio
  // call, no token needed
  useEffect(() => {
    setLoading(true);
    setErrorMsg("");
    getProjectsReadyForComparison()
      .then((projectList) => {
        setProjects(projectList);
        const comparisonCandidates = projectList.filter(
          (name) => !gtSets.includes(name)
        );

        if (comparisonCandidates.length > 0) {
          setComparisonProject((prev) =>
            comparisonCandidates.includes(prev) ? prev : comparisonCandidates[0]
          );
        } else {
          setComparisonProject("");
        }
      })
    .catch((e) => {
     setErrorMsg(e.message || "Failed to load projects.");
        setComparisonProject("");
      })
      .finally(() => setLoading(false));
  }, [gtSets]);

 // Load groundtruth sets that already have an evaluation for the
  // currently selected comparison project, a DB lookup against the evaluations table
  useEffect(() => {
    if (!comparisonProject) {
      setCompatibleGtSets([]);
      setGroundtruthProject("");
      return;
    }

    setCompatibleLoading(true);
    setCompatibleError("");

    getGroundtruthProjectsForComparison(comparisonProject)
      .then((names) => {
        setCompatibleGtSets(names);
        setGroundtruthProject((prev) => (names.includes(prev) ? prev : names[0] || ""));
      })
      .catch((e) => {
        setCompatibleGtSets([]);
        setGroundtruthProject("");
        setCompatibleError(e.message || "Failed to load compatible groundtruth sets.");
      })
      .finally(() => setCompatibleLoading(false));
  }, [comparisonProject]);

  const handleRunEvaluation = async () => {
    setEvalLoading(true);
    setEvalError("");
    setEvalResult(null);

    try {
      const result = await evaluateAI(
        token,
        groundtruthProject,
        comparisonProject
      );
      setEvalResult(result);
 } catch (e) {
      if (e.data?.error === "EVALUATION_NOT_FOUND") {
        setEvalError(
          "No evaluation exists yet for this pairing. If the run is finished, " +
          "this should appear automatically within moments — if it doesn't, " +
          "that likely points to a sync issue rather than something to retry."
        );
      } else {
        setEvalError(e.message || "Evaluation failed.");
      }
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
        < TokenLink />
        </div>

        <div className="mt-3">
          <label className="block text-sm font-medium mb-1">
            Label Studio Token
          </label>

          <input
            type="password"
            value={token}
            onChange={(e) => saveToken(e.target.value)}
            placeholder={token || "Enter your Label Studio token"}
            className="w-full border border-xtractyl-outline/30 rounded px-3 py-2 bg-xtractyl-white text-xtractyl-darktext"
            autoComplete="off"
            spellCheck={false}
          />
        </div>
      </div>

      {/* === SAVE AS GT SET === */}
      <SaveAsGtSet
        apiToken={token}
        onSuccess={() => setGtSetVersion(v => v + 1)}
      />

      {/* === COMPARISON SELECTION === */}
      <ComparisonSelection
        projects={projects}
        gtSets={gtSets}
        loading={loading}
        errorMsg={errorMsg}
        compatibleGtSets={compatibleGtSets}
        compatibleLoading={compatibleLoading}
        compatibleError={compatibleError}
        groundtruthProject={groundtruthProject}
        setGroundtruthProject={setGroundtruthProject}
        comparisonProject={comparisonProject}
        setComparisonProject={setComparisonProject}
        onSubmit={handleRunEvaluation}
      />

      {/* === EVALUATION RESULTS === */}
      {token && (
        <EvaluationResults
          loading={evalLoading}
          errorMsg={evalError}
          result={evalResult}
        />
      )}
    </div>
  );
}