import React, { useEffect, useState } from "react";

const DEFAULT_EXAMPLE = `You are a pure extraction model.

When you are given a TEXT and a QUESTION, you must return exactly one literal text passage from the TEXT that best answers the QUESTION.

Output format (mandatory):
- Return EXACTLY ONE matching passage, with no introduction, no explanations, no Markdown, NO JSON, and no quotation marks around the answer.
- Preserve capitalization, spaces, and punctuation EXACTLY as in the TEXT.
- If there is NO matching passage: respond with <<<NO_MATCH>>>.

Additional rules:
- Never provide multiple passages or variations.
- If multiple passages fit, choose the most precise and shortest exact passage.`;

/**
 * SystemPromptInput
 * Props:
 *  - value: string
 *  - onChange: (str) => void
 *  - placeholder?: string
 *  - exampleText?: string
 *  - persistKey?: string  // if provided, saves/restores from localStorage
 *  - maxLength?: number
 */
export default function SystemPromptInput({
  value,
  onChange,
  placeholder = "Enter the system prompt sent to the LLM…",
  exampleText = DEFAULT_EXAMPLE,
  persistKey,
  maxLength = 4000,
}) {
  const [open, setOpen] = useState(false);

  // optional persistence
  useEffect(() => {
    if (!persistKey) return;
    const saved = localStorage.getItem(persistKey);
    if (saved && !value) onChange(saved);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [persistKey]);

  useEffect(() => {
    if (!persistKey) return;
    try {
      localStorage.setItem(persistKey, value || "");
    } catch {}
  }, [value, persistKey]);

  const chars = value?.length || 0;

  return (
    <div>
      <label className="block font-medium mb-1">System prompt</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        maxLength={maxLength}
        rows={6}
        className="w-full p-3 border rounded"
      />
      <div className="mt-1 text-xs  text-xtractyl-outline/70">
        {chars}/{maxLength} characters
      </div>

      {/* Collapsible example */}
      <div className="mt-3">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="text-sm underline text-xtractyl-greenhover: text-xtractyl-green"
        >
          {open ? "Hide example" : "Show example"}
        </button>

        {open && (
          <div className="mt-2 bg-xtractyl-offwhite p-3 rounded border">
            <pre className="whitespace-pre-wrap text-sm">{exampleText}</pre>
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                onClick={() => onChange(exampleText)}
                className="px-3 py-2 rounded bg-xtractyl-green text-xtractyl-white hover:bg-xtractyl-green"
              >
                Use this example
              </button>
              <button
                type="button"
                onClick={() => navigator.clipboard?.writeText(exampleText)}
                className="px-3 py-2 rounded bg-xtractyl-offwhite hover:bg-xtractyl-offwhite"
              >
                Copy example
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}