// frontend/src/hooks/StartPrelabellingPage/usePrelabelConfig.js
import { useLocalStorage } from "./useLocalStorage";

export function usePrelabelConfig() {
  const [model, setModel] = useLocalStorage("ollamaModel", "");
  const [systemPrompt, setSystemPrompt] = useLocalStorage("xtractylSystemPrompt", "");

  return {
    model,
    setModel,
    systemPrompt,
    setSystemPrompt,
  };
}
