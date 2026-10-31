// src/components/EvaluateAIPage/EvaluateAICard.jsx
import { useState } from "react";
import { evaluateAI } from "../../api/EvaluateAIPage/api.js";
import SaveAsGtSet from "./SaveAsGtSet.jsx";
import ComparisonSelection from "./ComparisonSelection.jsx";
import EvaluationResults from "./EvaluationResults.jsx";
import { useAppContext } from "../../context/AppContext";
import TokenInput from "../shared/TokenInput";
import { useComparisonProjects } from "../../hooks/EvaluateAIPage/useComparisonProjects.js";
import { useCompatibleGroundtruthSets } from "../../hooks/EvaluateAIPage/useCompatibleGroundtruthSets.js";

export default function EvaluateAICard() {
  const { token } = useAppContext();
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalError, setEvalError] = useState("");
  const [evalResult, setEvalResult] = useState(null);
  const [gtSetVersion, setGtSetVersion] = useState(0);

  const { projects, loading, errorMsg, comparisonProject, setComparisonProject } =
    useComparisonProjects(gtSetVersion);

  const {
    compatibleGtSets,
    compatibleLoading,
    compatibleError,
    groundtruthProject,
    setGroundtruthProject,
  } = useCompatibleGroundtruthSets(comparisonProject, gtSetVersion);

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
