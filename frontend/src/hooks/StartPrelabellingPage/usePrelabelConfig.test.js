// src/hooks/StartPrelabellingPage/usePrelabelConfig.test.js
import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePrelabelConfig } from "./usePrelabelConfig.js";

describe("usePrelabelConfig", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("restores model and system prompt from storage", () => {
    localStorage.setItem("ollamaModel", "llama3");
    localStorage.setItem("xtractylSystemPrompt", "Extract.");

    const { result } = renderHook(() => usePrelabelConfig());

    expect(result.current.model).toBe("llama3");
    expect(result.current.systemPrompt).toBe("Extract.");
  });

  it("persists changes under the same keys", () => {
    const { result } = renderHook(() => usePrelabelConfig());

    act(() => {
      result.current.setModel("gemma");
      result.current.setSystemPrompt("Only the answer.");
    });

    expect(localStorage.getItem("ollamaModel")).toBe("gemma");
    expect(localStorage.getItem("xtractylSystemPrompt")).toBe("Only the answer.");
  });
});
