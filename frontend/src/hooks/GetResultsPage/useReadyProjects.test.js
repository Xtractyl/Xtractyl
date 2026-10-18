// frontend/src/hooks/GetResultsPage/useReadyProjects.test.js  (neu)
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useReadyProjects } from "./useReadyProjects.js";
import { getProjectsReadyForResults } from "../../api/GetResultsPage/api.js";

vi.mock("../../api/GetResultsPage/api.js");

describe("useReadyProjects", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("loads the projects once on mount", async () => {
    getProjectsReadyForResults.mockResolvedValue(["a", "b"]);

    const { result } = renderHook(() => useReadyProjects());

    expect(result.current.projects).toEqual([]);
    await waitFor(() => expect(result.current.projects).toEqual(["a", "b"]));
    expect(result.current.err).toBe("");
    expect(getProjectsReadyForResults).toHaveBeenCalledTimes(1);
  });

  it("returns an empty list and the error message when loading fails", async () => {
    getProjectsReadyForResults.mockRejectedValue(new Error("down"));

    const { result } = renderHook(() => useReadyProjects());

    await waitFor(() => expect(result.current.err).toBe("down"));
    expect(result.current.projects).toEqual([]);
  });

  it("uses a default message when the error has none", async () => {
    getProjectsReadyForResults.mockRejectedValue(new Error(""));

    const { result } = renderHook(() => useReadyProjects());

    await waitFor(() => expect(result.current.err).toBe("Failed to load projects."));
  });
});
