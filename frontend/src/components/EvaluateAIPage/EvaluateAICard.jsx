// src/components/EvaluateAIPage/EvaluateAICard.jsx
import { useState } from "react";
import SaveAsGtSet from "./SaveAsGtSet.jsx";
import ComparisonSelection from "./ComparisonSelection.jsx";
import EvaluationResults from "./EvaluationResults.jsx";
import { useAppContext } from "../../context/AppContext";
import TokenInput from "../shared/TokenInput";
import { useComparisonProjects } from "../../hooks/EvaluateAIPage/useComparisonProjects.js";
import { useCompatibleGroundtruthSets } from "../../hooks/EvaluateAIPage/useCompatibleGroundtruthSets.js";
import { useEvaluation } from "../../hooks/EvaluateAIPage/useEvaluation.js";

export default function EvaluateAICard() {
  const { token } = useAppContext();
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

  const { evalLoading, evalError, evalResult, runEvaluation } = useEvaluation();

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
        onSubmit={() => runEvaluation(groundtruthProject, comparisonProject)}
      />

      {/* === EVALUATION RESULTS === */}
      <EvaluationResults loading={evalLoading} errorMsg={evalError} result={evalResult} />
    </div>
  );
}
