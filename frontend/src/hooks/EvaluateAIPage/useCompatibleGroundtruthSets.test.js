// frontend/src/hooks/EvaluateAIPage/useCompatibleGroundtruthSets.test.js
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useCompatibleGroundtruthSets } from "./useCompatibleGroundtruthSets.js";
import { getGroundtruthProjectsForComparison } from "../../api/EvaluateAIPage/api.js";

vi.mock("../../api/EvaluateAIPage/api.js");

function renderSets(initialProps = { comparison: "cmp", key: 0 }) {
  return renderHook(({ comparison, key }) => useCompatibleGroundtruthSets(comparison, key), {
    initialProps,
  });
}

describe("useCompatibleGroundtruthSets", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("does nothing without a comparison project", () => {
    const { result } = renderSets({ comparison: "", key: 0 });

    expect(getGroundtruthProjectsForComparison).not.toHaveBeenCalled();
    expect(result.current.compatibleGtSets).toEqual([]);
    expect(result.current.groundtruthProject).toBe("");
    expect(result.current.compatibleLoading).toBe(false);
  });

  it("loads the sets for the comparison project and selects the first one", async () => {
    getGroundtruthProjectsForComparison.mockResolvedValue(["gt1", "gt2"]);

    const { result } = renderSets();

    await waitFor(() => expect(result.current.compatibleGtSets).toEqual(["gt1", "gt2"]));
    expect(getGroundtruthProjectsForComparison).toHaveBeenCalledWith("cmp");
    expect(result.current.groundtruthProject).toBe("gt1");
    expect(result.current.compatibleError).toBe("");
  });

  it("is loading until the request has finished", async () => {
    let resolve;
    getGroundtruthProjectsForComparison.mockReturnValue(
      new Promise((r) => {
        resolve = r;
      })
    );

    const { result } = renderSets();

    expect(result.current.compatibleLoading).toBe(true);

    await act(async () => resolve(["gt1"]));

    expect(result.current.compatibleLoading).toBe(false);
  });

  it("selects nothing when no set is compatible", async () => {
    getGroundtruthProjectsForComparison.mockResolvedValue([]);

    const { result } = renderSets();

    await waitFor(() => expect(result.current.compatibleLoading).toBe(false));
    expect(result.current.compatibleGtSets).toEqual([]);
    expect(result.current.groundtruthProject).toBe("");
  });

  it("lets the caller change the selected set", async () => {
    getGroundtruthProjectsForComparison.mockResolvedValue(["gt1", "gt2"]);

    const { result } = renderSets();
    await waitFor(() => expect(result.current.groundtruthProject).toBe("gt1"));

    act(() => result.current.setGroundtruthProject("gt2"));

    expect(result.current.groundtruthProject).toBe("gt2");
  });

  it("loads the sets of the new comparison project when it changes", async () => {
    getGroundtruthProjectsForComparison.mockResolvedValueOnce(["gt1"]);
    const { result, rerender } = renderSets();
    await waitFor(() => expect(result.current.compatibleGtSets).toEqual(["gt1"]));

    getGroundtruthProjectsForComparison.mockResolvedValueOnce(["gt9"]);
    rerender({ comparison: "other", key: 0 });

    await waitFor(() => expect(result.current.compatibleGtSets).toEqual(["gt9"]));
    expect(getGroundtruthProjectsForComparison).toHaveBeenLastCalledWith("other");
    expect(result.current.groundtruthProject).toBe("gt9");
  });

  it("resets everything when the comparison project is cleared", async () => {
    getGroundtruthProjectsForComparison.mockResolvedValue(["gt1"]);
    const { result, rerender } = renderSets();
    await waitFor(() => expect(result.current.groundtruthProject).toBe("gt1"));

    rerender({ comparison: "", key: 0 });

    await waitFor(() => expect(result.current.compatibleGtSets).toEqual([]));
    expect(result.current.groundtruthProject).toBe("");
  });

  it("reloads when reloadKey changes and keeps the selection if it still exists", async () => {
    getGroundtruthProjectsForComparison.mockResolvedValueOnce(["gt1", "gt2"]);
    const { result, rerender } = renderSets();
    await waitFor(() => expect(result.current.groundtruthProject).toBe("gt1"));
    act(() => result.current.setGroundtruthProject("gt2"));

    getGroundtruthProjectsForComparison.mockResolvedValueOnce(["gt1", "gt2", "gt3"]);
    rerender({ comparison: "cmp", key: 1 });

    await waitFor(() => expect(result.current.compatibleGtSets).toEqual(["gt1", "gt2", "gt3"]));
    expect(getGroundtruthProjectsForComparison).toHaveBeenCalledTimes(2);
    expect(result.current.groundtruthProject).toBe("gt2");
  });

  it("falls back to the first set when the selected one is gone after a reload", async () => {
    getGroundtruthProjectsForComparison.mockResolvedValueOnce(["gt1", "gt2"]);
    const { result, rerender } = renderSets();
    await waitFor(() => expect(result.current.groundtruthProject).toBe("gt1"));
    act(() => result.current.setGroundtruthProject("gt2"));

    getGroundtruthProjectsForComparison.mockResolvedValueOnce(["gt1", "gt3"]);
    rerender({ comparison: "cmp", key: 1 });

    await waitFor(() => expect(result.current.compatibleGtSets).toEqual(["gt1", "gt3"]));
    expect(result.current.groundtruthProject).toBe("gt1");
  });

  it("returns the error message and clears sets and selection when loading fails", async () => {
    getGroundtruthProjectsForComparison.mockRejectedValue(new Error("down"));

    const { result } = renderSets();

    await waitFor(() => expect(result.current.compatibleError).toBe("down"));
    expect(result.current.compatibleGtSets).toEqual([]);
    expect(result.current.groundtruthProject).toBe("");
    expect(result.current.compatibleLoading).toBe(false);
  });

  it("uses a default message when the error has none", async () => {
    getGroundtruthProjectsForComparison.mockRejectedValue(new Error(""));

    const { result } = renderSets();

    await waitFor(() =>
      expect(result.current.compatibleError).toBe("Failed to load compatible groundtruth sets.")
    );
  });
});
