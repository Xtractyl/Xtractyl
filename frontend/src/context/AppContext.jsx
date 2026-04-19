// /src/context/AppContext.jsx 
import { createContext, useContext, useState } from "react";

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

  return (
    <AppContext.Provider value={{ token, projectName, saveToken, saveProjectName }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  return useContext(AppContext);  
}