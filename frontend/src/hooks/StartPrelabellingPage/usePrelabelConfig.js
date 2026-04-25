// frontend/src/hooks/StartPrelabellingPage/usePrelabelConfig.js
import { useState } from "react";
import { useLocalStorage } from "./useLocalStorage";

export function usePrelabelConfig() {
  const [model, setModel] = useLocalStorage("ollamaModel", "");
  const [systemPrompt, setSystemPrompt] = useLocalStorage("xtractylSystemPrompt", "");
  const [qalFile, setQalFile] = useLocalStorage("xtractylQALFile", "");
  const [questionsAndLabels, setQuestionsAndLabels] = useState({});

  const handleQalChange = (_project, file, json) => {
    setQalFile(file);
    setQuestionsAndLabels(json);
  };

  return {
    model, setModel,
    systemPrompt, setSystemPrompt,
    qalFile,
    questionsAndLabels,
    handleQalChange,
  };
}