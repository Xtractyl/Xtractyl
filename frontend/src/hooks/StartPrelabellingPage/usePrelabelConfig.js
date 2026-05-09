// frontend/src/hooks/StartPrelabellingPage/usePrelabelConfig.js
import { useState, useEffect, useRef } from "react";
import { useLocalStorage } from "./useLocalStorage";
import { previewQal } from "../../api/StartPrelabellingPage/api.js";
import { useAppContext } from "../../context/AppContext";


export function usePrelabelConfig() {
  const loadedRef = useRef(false);
  const { projectName } = useAppContext();
  const [model, setModel] = useLocalStorage("ollamaModel", "");
  const [systemPrompt, setSystemPrompt] = useLocalStorage("xtractylSystemPrompt", "");
  const [qalFile, setQalFile] = useLocalStorage("xtractylQALFile", "");
  const [questionsAndLabels, setQuestionsAndLabels] = useState({});

  useEffect(() => {
    if (!qalFile || !projectName || loadedRef.current) return;
    loadedRef.current = true;
    previewQal(projectName, qalFile)
      .then((json) => setQuestionsAndLabels(json?.data ?? json))
      .catch(() => {});
  }, [qalFile, projectName]);

  const handleQalChange = (_project, file, json) => {
    setQalFile(file);
    setQuestionsAndLabels(json?.data ?? json);
  };

  return {
    model, setModel,
    systemPrompt, setSystemPrompt,
    qalFile,
    questionsAndLabels,
    handleQalChange,
  };
}