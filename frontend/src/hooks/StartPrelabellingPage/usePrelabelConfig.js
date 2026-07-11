// frontend/src/hooks/StartPrelabellingPage/usePrelabelConfig.js
import { useState, useEffect } from "react";
import { useLocalStorage } from "./useLocalStorage";
import { previewQal } from "../../api/StartPrelabellingPage/api.js";
import { useAppContext } from "../../context/AppContext";


export function usePrelabelConfig() {
  const { projectName } = useAppContext();
  const [model, setModel] = useLocalStorage("ollamaModel", "");
  const [systemPrompt, setSystemPrompt] = useLocalStorage("xtractylSystemPrompt", "");
  const [questionsAndLabels, setQuestionsAndLabels] = useState({});
  const [qalError, setQalError] = useState("");

  useEffect(() => {
    if (!projectName) return;
    setQalError("");
    previewQal(projectName)
      .then((json) => setQuestionsAndLabels(json?.data ?? json))
      .catch(() => {
        setQuestionsAndLabels({});
        setQalError(`No questions/labels found for project "${projectName}". Go to Create Project to add them first.`);
      });
  }, [projectName]);



  return {
    model, setModel,
    systemPrompt, setSystemPrompt,
    questionsAndLabels,
    qalError,
  };
}