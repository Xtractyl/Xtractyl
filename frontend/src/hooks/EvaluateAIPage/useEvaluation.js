// frontend/src/hooks/EvaluateAIPage/useEvaluation.js
import { useState } from "react";
import { evaluateAI } from "../../api/EvaluateAIPage/api.js";

export function useEvaluation() {
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalError, setEvalError] = useState("");
  const [evalResult, setEvalResult] = useState(null);

  const runEvaluation = async (groundtruthProject, comparisonProject) => {
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

  return { evalLoading, evalError, evalResult, runEvaluation };
}
