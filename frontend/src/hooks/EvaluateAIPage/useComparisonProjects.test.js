// frontend/src/hooks/EvaluateAIPage/useComparisonProjects.test.js
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useComparisonProjects } from "./useComparisonProjects.js";
import { getProjectsReadyForComparison } from "../../api/EvaluateAIPage/api.js";

vi.mock("../../api/EvaluateAIPage/api.js");

describe("useComparisonProjects", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("loads the projects on mount and selects the first one", async () => {
    getProjectsReadyForComparison.mockResolvedValue(["a", "b"]);

    const { result } = renderHook(() => useComparisonProjects(0));

    await waitFor(() => expect(result.current.projects).toEqual(["a", "b"]));
    expect(result.current.comparisonProject).toBe("a");
    expect(result.current.errorMsg).toBe("");
    expect(getProjectsReadyForComparison).toHaveBeenCalledTimes(1);
  });

  it("is loading until the request has finished", async () => {
    let resolve;
    getProjectsReadyForComparison.mockReturnValue(
      new Promise((r) => {
        resolve = r;
      })
    );

    const { result } = renderHook(() => useComparisonProjects(0));

    expect(result.current.loading).toBe(true);

    await act(async () => resolve(["a"]));

    expect(result.current.loading).toBe(false);
  });

  it("selects nothing when there are no projects", async () => {
    getProjectsReadyForComparison.mockResolvedValue([]);

    const { result } = renderHook(() => useComparisonProjects(0));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.projects).toEqual([]);
    expect(result.current.comparisonProject).toBe("");
  });

  it("lets the caller change the selected project", async () => {
    getProjectsReadyForComparison.mockResolvedValue(["a", "b"]);

    const { result } = renderHook(() => useComparisonProjects(0));
    await waitFor(() => expect(result.current.comparisonProject).toBe("a"));

    act(() => result.current.setComparisonProject("b"));

    expect(result.current.comparisonProject).toBe("b");
  });

  it("reloads when reloadKey changes and keeps the selection if it still exists", async () => {
    getProjectsReadyForComparison.mockResolvedValueOnce(["a", "b"]);
    const { result, rerender } = renderHook(({ key }) => useComparisonProjects(key), {
      initialProps: { key: 0 },
    });
    await waitFor(() => expect(result.current.comparisonProject).toBe("a"));
    act(() => result.current.setComparisonProject("b"));

    getProjectsReadyForComparison.mockResolvedValueOnce(["a", "b", "c"]);
    rerender({ key: 1 });

    await waitFor(() => expect(result.current.projects).toEqual(["a", "b", "c"]));
    expect(getProjectsReadyForComparison).toHaveBeenCalledTimes(2);
    expect(result.current.comparisonProject).toBe("b");
  });

  it("falls back to the first project when the selected one is gone after a reload", async () => {
    getProjectsReadyForComparison.mockResolvedValueOnce(["a", "b"]);
    const { result, rerender } = renderHook(({ key }) => useComparisonProjects(key), {
      initialProps: { key: 0 },
    });
    await waitFor(() => expect(result.current.comparisonProject).toBe("a"));
    act(() => result.current.setComparisonProject("b"));

    getProjectsReadyForComparison.mockResolvedValueOnce(["a", "c"]);
    rerender({ key: 1 });

    await waitFor(() => expect(result.current.projects).toEqual(["a", "c"]));
    expect(result.current.comparisonProject).toBe("a");
  });

  it("returns the error message and clears the selection when loading fails", async () => {
    getProjectsReadyForComparison.mockRejectedValue(new Error("down"));

    const { result } = renderHook(() => useComparisonProjects(0));

    await waitFor(() => expect(result.current.errorMsg).toBe("down"));
    expect(result.current.comparisonProject).toBe("");
    expect(result.current.loading).toBe(false);
  });

  it("uses a default message when the error has none", async () => {
    getProjectsReadyForComparison.mockRejectedValue(new Error(""));

    const { result } = renderHook(() => useComparisonProjects(0));

    await waitFor(() => expect(result.current.errorMsg).toBe("Failed to load projects."));
  });
});
