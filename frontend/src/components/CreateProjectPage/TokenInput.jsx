import { useState, useEffect } from "react";

const LS_BASE = import.meta.env.VITE_LS_BASE || "http://localhost:8080";

export default function TokenInput({ onTokenSave }) {
  const [token, setToken] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("apiToken");
    if (saved) setToken(saved);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = token.trim();
    if (!trimmed) return;

    onTokenSave?.(trimmed);
    localStorage.setItem("apiToken", trimmed);
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 bg-xtractyl-offwhite rounded shadow w-full space-y-4">
      <label htmlFor="ls-token" className="block text-sm font-medium mb-2">
        Enter your Label Studio legacy token
      </label>
      <input
        type="password"
        id="ls-token"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        placeholder="Paste your legacy token"
        className="w-full px-3 py-2 border rounded mb-3"
        autoComplete="off"
        spellCheck={false}
      />
      <button
        type="submit"
        className="bg-xtractyl-orange text-white px-4 py-2 rounded hover:bg-xtractyl-orange-600 transition"
      >
        Save Token
      </button>

      {/* Token helper + Eingabe */}
      <div className="mt-4">
        <a
          href={`${LS_BASE}/user/account/legacy-token`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-xtractyl-orange text-white text-base font-medium px-5 py-2 rounded shadow hover:bg-xtractyl-orange-600 transition"
        >
          Get your legacy token
        </a>
        <p className="mt-2 text-sm text-gray-500">
          Return here after copying the token from Label Studio.
        </p>
        <p className="mt-1 text-sm text-gray-500">
          ⚠️ If you see no legacy token there, go to{" "}
          <a
            href={`${LS_BASE}/organization`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#6baa56] hover:underline"
          >
            {LS_BASE}/organization
          </a>{" "}
          and enable it via the API Tokens settings.
        </p>
      </div>
    </form>
  );
}