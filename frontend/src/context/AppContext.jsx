// /src/context/AppContext.jsx 
import { createContext, useContext, useEffect, useState } from "react";
import { pullModel } from "../api/StartPrelabellingPage/api.js";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [token, setToken] = useState(
    () => localStorage.getItem("apiToken") ?? ""
  );
  const [projectName, setProjectName] = useState(
    () => localStorage.getItem("projectName") ?? ""
  );

  const saveToken = (t) => {
    setToken(t);
    localStorage.setItem("apiToken", t);
  };

  const saveProjectName = (name) => {
    setProjectName(name);
    localStorage.setItem("projectName", name);
  };


  const [pulling, setPulling] = useState(false);
  const [pullingModel, setPullingModel] = useState("");
  const [pullProgress, setPullProgress] = useState("");
  const [pullError, setPullError] = useState("");

  useEffect(() => {
    if (!pulling) return;
    const handleBeforeUnload = (e) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [pulling]);

  const startModelPull = async (model) => {
    if (pulling) return false;
    setPullingModel(model);
    setPulling(true);
    setPullProgress("Starting…");
    setPullError("");

    try {
      await pullModel(model, setPullProgress);
      setPullProgress("Done");
      return true;
    } catch (e) {
      setPullError(e.message || "Unknown error");
      return false;
    } finally {
      setPulling(false);
    }
  };

  const resetPullError = () => setPullError("");

  return (
    <AppContext.Provider
      value={{
        token,
        projectName,
        saveToken,
        saveProjectName,
        pulling,
        pullingModel,
        pullProgress,
        pullError,
        startModelPull,
        resetPullError,
      }}
    >
    {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  return useContext(AppContext);  
}