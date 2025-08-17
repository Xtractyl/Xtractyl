import { useState } from "react";

export default function useError() {
  const [error, setError] = useState("");
  const clearError = () => setError("");
  return { error, setError, clearError };
}