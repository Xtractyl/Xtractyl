// frontend/src/hooks/EvaluateAIPage/useCompatibleGroundtruthSets.js
import { useEffect, useState } from "react";
import { getGroundtruthProjectsForComparison } from "../../api/EvaluateAIPage/api.js";

export function useCompatibleGroundtruthSets(comparisonProject, reloadKey) {
  const [compatibleGtSets, setCompatibleGtSets] = useState([]);
  const [compatibleLoading, setCompatibleLoading] = useState(false);
  const [compatibleError, setCompatibleError] = useState("");
  const [groundtruthProject, setGroundtruthProject] = useState("");

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
  }, [comparisonProject, reloadKey]);

  return {
    compatibleGtSets,
    compatibleLoading,
    compatibleError,
    groundtruthProject,
    setGroundtruthProject,
  };
}
