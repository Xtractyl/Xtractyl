import { useState } from "react";

export default function useToken(onTokenSave) {
  const [token, setToken] = useState(() => {
    return localStorage.getItem("apiToken") || "";
  });

  const saveToken = (newToken) => {
    setToken(newToken);
    try { localStorage.setItem("apiToken", newToken); } catch {}
    if (onTokenSave) onTokenSave(newToken);
  };

  return { token, saveToken };
}