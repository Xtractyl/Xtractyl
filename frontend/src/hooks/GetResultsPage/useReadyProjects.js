// frontend/src/hooks/GetResultsPage/useReadyProjects.js
import { useEffect, useState } from "react";
import { getProjectsReadyForResults } from "../../api/GetResultsPage/api.js";

export function useReadyProjects() {
  const [projects, setProjects] = useState([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    getProjectsReadyForResults()
      .then(setProjects)
      .catch((e) => {
        setProjects([]);
        setErr(e.message || "Failed to load projects.");
      });
  }, []);

  return { projects, err };
}
