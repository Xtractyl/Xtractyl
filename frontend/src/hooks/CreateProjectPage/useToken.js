import { useState, useEffect } from "react";

export default function useToken(onTokenSave) {
  const [token, setToken] = useState(() => {
    return localStorage.getItem("lsToken") || "";
  });

  const saveToken = (newToken) => {
    setToken(newToken);
    try { localStorage.setItem("lsToken", newToken); } catch {}
    if (onTokenSave) onTokenSave(newToken);
  };

  return { token, saveToken };
}