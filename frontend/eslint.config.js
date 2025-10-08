// eslint.config.js (frontend/)
import js from "@eslint/js";
import importPlugin from "eslint-plugin-import";
import globals from "globals";

export default [
  js.configs.recommended,
  {
    ignores: ["dist/**", "build/**", ".vite/**", "coverage/**", "node_modules/**"],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
      globals: {
        ...globals.browser, // enables fetch, AbortController, FormData, etc.
      },
    },
    plugins: { import: importPlugin },
    rules: {
      "no-undef": "error",
      "import/no-unresolved": "error",
      "no-unused-vars": [
        "error",
        {
          args: "after-used",
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
        },
      ],
      "no-empty": ["error", { allowEmptyCatch: true }],
    },
  },
];