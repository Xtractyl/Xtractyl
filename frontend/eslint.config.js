// eslint.config.js (frontend/)
import js from "@eslint/js";
import importPlugin from "eslint-plugin-import";
import globals from "globals";
import reactPlugin from "eslint-plugin-react";
import reactHooksPlugin from "eslint-plugin-react-hooks"; 

export default [
  js.configs.recommended,
  {
    files: ["**/*.{js,jsx}"],
    ignores: ["dist/**", "build/**", ".vite/**", "coverage/**", "node_modules/**"],
    languageOptions: {
  ecmaVersion: 2023,
  sourceType: "module",
  parserOptions: {
    ecmaFeatures: {
      jsx: true,  // ← das fehlt!
    },
  },
  globals: {
    ...globals.browser,
  },
},
    plugins: { import: importPlugin,
      react: reactPlugin,
      "react-hooks": reactHooksPlugin, 
     },
    rules: {
       "import/no-unresolved": "off", 
      "no-undef": "error",
      "no-unused-vars": [
        "error",
        {
          args: "after-used",
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
        },
      ],
      "no-empty": ["error", { allowEmptyCatch: true }],
        "object-shorthand": "warn", 
        "react/jsx-uses-react": "error",
        "react/jsx-uses-vars": "error",   
        "react-hooks/exhaustive-deps": "warn", 
    },
  },
];