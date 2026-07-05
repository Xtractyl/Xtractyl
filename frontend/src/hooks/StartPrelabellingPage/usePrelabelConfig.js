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
  const [questionsAndLabels, setQuestionsAndLabels] = useState({});

  useEffect(() => {
    if (!projectName || loadedRef.current) return;
    loadedRef.current = true;
    previewQal(projectName)
      .then((json) => setQuestionsAndLabels(json?.data ?? json))
      .catch(() => {});
  }, [projectName]);



  return {
    model, setModel,
    systemPrompt, setSystemPrompt,
    questionsAndLabels,
  };
}