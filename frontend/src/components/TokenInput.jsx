import { useState } from "react";

export default function TokenInput({ onTokenSave }) {
  const [token, setToken] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (token.trim()) {
      onTokenSave(token.trim()); // Übergibt den Token an App.jsx
      setToken(""); // Optional: Eingabefeld leeren
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 bg-beige rounded shadow">
      <label className="block text-sm font-medium mb-2">
        Enter your Label Studio token:
      </label>
      <input
        type="text"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        placeholder="Your token"
        className="w-full px-3 py-2 border rounded mb-3"
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