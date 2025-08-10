import { useState, useEffect } from "react";

export default function TokenInput({ onTokenSave }) {
  const [token, setToken] = useState("");

  // Prefill from localStorage if available
  useEffect(() => {
    const saved = localStorage.getItem("apiToken");
    if (saved) setToken(saved);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = token.trim();
    if (!trimmed) return;

    // Pass token up to the parent (App.jsx) and persist locally
    onTokenSave?.(trimmed);
    localStorage.setItem("apiToken", trimmed);
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 bg-beige rounded shadow w-full">
      <label htmlFor="ls-token" className="block text-sm font-medium mb-2">
        Enter your Label Studio legacy token
      </label>
      <input
        id="ls-token"
        type="text"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        placeholder="Paste your legacy token"
        className="w-full px-3 py-2 border rounded mb-3"
        autoComplete="off"
        spellCheck={false}
      />
      <button
        type="submit"
        className="bg-xtractyl-orange text-white px-4 py-2 rounded hover:bg-orange-600 transition"
      >
        Save Token
      </button>
    </form>
  );
}