// src/components/EvaluateAIPage/EvaluateAICard.jsx
import { useEffect, useState } from "react";
import { fetchEvaluationProjects, evaluateAI } from "../../api/EvaluateAIPage/api.js";
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

  // Load project names from Label Studio via orchestrator
  useEffect(() => {
    if (!token) return;

    setLoading(true);
    setErrorMsg("");

    fetchEvaluationProjects(token)
      .then((names) => {
        const projectList = names || [];
        setProjects(projectList);

        const defaultGT = gtSets[0] || "";
        setGroundtruthProject((prev) => prev || defaultGT);

        const comparisonCandidates = projectList.filter(
          (name) => !gtSets.includes(name)
        );

        if (comparisonCandidates.length > 0) {
          setComparisonProject((prev) => prev || comparisonCandidates[0]);
        } else {
          setComparisonProject("");
        }
      })
    .catch((e) => {
     setErrorMsg(e.message || "Failed to load Label Studio projects.");
        setGroundtruthProject(gtSets[0] || "");
        setComparisonProject("");
      })
      .finally(() => setLoading(false));
  }, [token, gtSets]);

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
   setEvalError(e.message || "Evaluation failed.");
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
      {token && (
        <SaveAsGtSet
          apiToken={token}
          projects={projects}
          gtSets={gtSets}
          onSuccess={() => setGtSetVersion(v => v + 1)}
        />
      )}

      {/* === COMPARISON SELECTION === */}
      {token && (
        <ComparisonSelection
          projects={projects}
          gtSets={gtSets}
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