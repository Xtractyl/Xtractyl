// frontend/src/hooks/StartPrelabellingPage/useLocalStorage.js
import { useState, useEffect } from "react";

export function useLocalStorage(key, defaultValue) {
  const [value, setValue] = useState(
    () => localStorage.getItem(key) ?? defaultValue
  );

  useEffect(() => {
    try { localStorage.setItem(key, value); } catch {}
  }, [key, value]);

  return [value, setValue];
}