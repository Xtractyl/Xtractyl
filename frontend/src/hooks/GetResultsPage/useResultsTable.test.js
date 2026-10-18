// frontend/src/hooks/GetResultsPage/useResultsTable.test.js  (neu)
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useResultsTable } from "./useResultsTable.js";
import { getResultsTable } from "../../api/GetResultsPage/api.js";

vi.mock("../../api/GetResultsPage/api.js");

const TABLE = {
  columns: ["task_id", "filename"],
  rows: [{ task_id: 1, filename: "a.html" }],
  total: 1,
};

describe("useResultsTable", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("starts empty and idle", () => {
    const { result } = renderHook(() => useResultsTable());

    expect(result.current.columns).toEqual([]);
    expect(result.current.rows).toEqual([]);
    expect(result.current.loading).toBe(false);
    expect(result.current.err).toBe("");
  });

  it("load fetches the table for the project and stores columns and rows", async () => {
    getResultsTable.mockResolvedValue(TABLE);
    const { result } = renderHook(() => useResultsTable());

    await act(async () => {
      await result.current.load("proj");
    });

    expect(getResultsTable).toHaveBeenCalledWith({ projectName: "proj" });
    expect(result.current.columns).toEqual(TABLE.columns);
    expect(result.current.rows).toEqual(TABLE.rows);
    expect(result.current.loading).toBe(false);
    expect(result.current.err).toBe("");
  });

  it("is loading while the request is pending", async () => {
    let resolve;
    getResultsTable.mockReturnValue(new Promise((r) => (resolve = r)));
    const { result } = renderHook(() => useResultsTable());

    let pending;
    act(() => {
      pending = result.current.load("proj");
    });
    expect(result.current.loading).toBe(true);

    await act(async () => {
      resolve(TABLE);
      await pending;
    });
    expect(result.current.loading).toBe(false);
  });

  it("stores the error message and empties the data when the request fails", async () => {
    getResultsTable.mockRejectedValue(new Error("RUN_NOT_DONE"));
    const { result } = renderHook(() => useResultsTable());

    await act(async () => {
      await result.current.load("proj");
    });

    expect(result.current.err).toBe("RUN_NOT_DONE");
    expect(result.current.columns).toEqual([]);
    expect(result.current.rows).toEqual([]);
    expect(result.current.loading).toBe(false);
  });

  it("uses a default message when the error has none", async () => {
    getResultsTable.mockRejectedValue(new Error(""));
    const { result } = renderHook(() => useResultsTable());

    await act(async () => {
      await result.current.load("proj");
    });

    expect(result.current.err).toBe("Request failed");
  });

  it("drops previously loaded data when a later load fails", async () => {
    getResultsTable.mockResolvedValueOnce(TABLE).mockRejectedValueOnce(new Error("boom"));
    const { result } = renderHook(() => useResultsTable());

    await act(async () => {
      await result.current.load("proj");
    });
    await act(async () => {
      await result.current.load("proj");
    });

    expect(result.current.rows).toEqual([]);
    expect(result.current.err).toBe("boom");
  });

  it("reset clears columns, rows and error", async () => {
    getResultsTable.mockResolvedValueOnce(TABLE).mockRejectedValueOnce(new Error("boom"));
    const { result } = renderHook(() => useResultsTable());

    await act(async () => {
      await result.current.load("proj");
    });
    act(() => result.current.reset());
    expect(result.current.columns).toEqual([]);
    expect(result.current.rows).toEqual([]);

    await act(async () => {
      await result.current.load("proj");
    });
    expect(result.current.err).toBe("boom");

    act(() => result.current.reset());
    expect(result.current.err).toBe("");
  });
});
