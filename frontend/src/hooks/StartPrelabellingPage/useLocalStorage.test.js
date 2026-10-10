// src/hooks/StartPrelabellingPage/useLocalStorage.test.js
import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useLocalStorage } from "./useLocalStorage.js";

describe("useLocalStorage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns the default value when nothing is stored", () => {
    const { result } = renderHook(() => useLocalStorage("key", "fallback"));

    expect(result.current[0]).toBe("fallback");
  });

  it("writes the default value to storage on mount", () => {
    renderHook(() => useLocalStorage("key", "fallback"));

    expect(localStorage.getItem("key")).toBe("fallback");
  });

  it("returns the stored value instead of the default", () => {
    localStorage.setItem("key", "stored");

    const { result } = renderHook(() => useLocalStorage("key", "fallback"));

    expect(result.current[0]).toBe("stored");
  });

  it("treats a stored empty string as a value and not as missing", () => {
    localStorage.setItem("key", "");

    const { result } = renderHook(() => useLocalStorage("key", "fallback"));

    expect(result.current[0]).toBe("");
  });

  it("writes changes to storage", () => {
    const { result } = renderHook(() => useLocalStorage("key", ""));

    act(() => {
      result.current[1]("changed");
    });

    expect(result.current[0]).toBe("changed");
    expect(localStorage.getItem("key")).toBe("changed");
  });
});
