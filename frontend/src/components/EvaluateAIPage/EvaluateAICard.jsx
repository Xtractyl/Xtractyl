// src/components/EvaluateAIPage/EvaluateAICard.jsx
import { useEffect, useState } from "react";
import { getGroundtruthProjectsForComparison, evaluateAI } from "../../api/EvaluateAIPage/api.js";
import SaveAsGtSet from "./SaveAsGtSet.jsx";
import ComparisonSelection from "./ComparisonSelection.jsx";
import EvaluationResults from "./EvaluationResults.jsx";
import { useAppContext } from "../../context/AppContext";
import TokenInput from "../shared/TokenInput";
import { useComparisonProjects } from "../../hooks/EvaluateAIPage/useComparisonProjects.js";

export default function EvaluateAICard() {
  const { token } = useAppContext();
  const [groundtruthProject, setGroundtruthProject] = useState("");
  const [compatibleGtSets, setCompatibleGtSets] = useState([]);
  const [compatibleLoading, setCompatibleLoading] = useState(false);
  const [compatibleError, setCompatibleError] = useState("");
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalError, setEvalError] = useState("");
  const [evalResult, setEvalResult] = useState(null);
  const [gtSetVersion, setGtSetVersion] = useState(0);

  const { projects, loading, errorMsg, comparisonProject, setComparisonProject } =
    useComparisonProjects(gtSetVersion);

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
      const result = await evaluateAI(groundtruthProject, comparisonProject);
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
        Select a groundtruth project and a prelabelled project on the same tasks to get evaluation
        metrics.
      </p>

      {/* === TOKEN SECTION === */}
      <div className="mt-8">
        <TokenInput />
      </div>

      {/* === SAVE AS GT SET === */}
      <SaveAsGtSet apiToken={token} onSuccess={() => setGtSetVersion((v) => v + 1)} />

      {/* === COMPARISON SELECTION === */}
      <ComparisonSelection
        projects={projects}
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
      <EvaluationResults loading={evalLoading} errorMsg={evalError} result={evalResult} />
    </div>
  );
}
