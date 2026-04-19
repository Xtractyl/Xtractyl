//src/components/CreateProjectPage/TokenInput.jsx
import { useAppContext } from "../../context/AppContext";
import TokenLink from "../shared/TokenLink";

const LS_BASE = import.meta.env.VITE_LS_BASE || "http://localhost:8080";

export default function TokenInput() {
  const { token, saveToken } = useAppContext();


  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = token.trim();
    if (!trimmed) return;

    onTokenSave?.(trimmed);
    saveToken(trimmed);
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
        onChange={(e) => saveToken(e.target.value)}
        placeholder="Paste your legacy token"
        className="w-full px-3 py-2 border border-xtractyl-outline/30 rounded mb-3 bg-xtractyl-white text-xtractyl-darktext"
        autoComplete="off"
        spellCheck={false}
      />
      <button
        type="submit"
        className="bg-xtractyl-orange text-xtractyl-white px-4 py-2 rounded hover:bg-xtractyl-orange/80 transition"
      >
        Save Token
      </button>

      {/* Token helper + Eingabe */}
      <div className="mt-4">
      < TokenLink />
      </div>
    </form>
  );
}