// frontend/src/hooks/EvaluateAIPage/useEvaluation.test.js
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useEvaluation } from "./useEvaluation.js";
import { evaluateAI } from "../../api/EvaluateAIPage/api.js";

vi.mock("../../api/EvaluateAIPage/api.js");

describe("useEvaluation", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("starts idle", () => {
    const { result } = renderHook(() => useEvaluation());

    expect(result.current.evalLoading).toBe(false);
    expect(result.current.evalError).toBe("");
    expect(result.current.evalResult).toBeNull();
  });

  it("requests the evaluation for the given pair and exposes the result", async () => {
    const data = { metrics: { micro: { f1: 1 } } };
    evaluateAI.mockResolvedValue(data);
    const { result } = renderHook(() => useEvaluation());

    await act(async () => {
      await result.current.runEvaluation("gt", "cmp");
    });

    expect(evaluateAI).toHaveBeenCalledWith("gt", "cmp");
    expect(result.current.evalResult).toEqual(data);
    expect(result.current.evalError).toBe("");
    expect(result.current.evalLoading).toBe(false);
  });

  it("is loading while the request is running", async () => {
    let resolve;
    evaluateAI.mockReturnValue(
      new Promise((r) => {
        resolve = r;
      })
    );
    const { result } = renderHook(() => useEvaluation());

    let pending;
    act(() => {
      pending = result.current.runEvaluation("gt", "cmp");
    });

    expect(result.current.evalLoading).toBe(true);

    await act(async () => {
      resolve({});
      await pending;
    });

    expect(result.current.evalLoading).toBe(false);
  });

  it("exposes the error message and no result when the request fails", async () => {
    evaluateAI.mockRejectedValue(new Error("not found"));
    const { result } = renderHook(() => useEvaluation());

    await act(async () => {
      await result.current.runEvaluation("gt", "cmp");
    });

    expect(result.current.evalError).toBe("not found");
    expect(result.current.evalResult).toBeNull();
    expect(result.current.evalLoading).toBe(false);
  });

  it("uses a default message when the error has none", async () => {
    evaluateAI.mockRejectedValue(new Error(""));
    const { result } = renderHook(() => useEvaluation());

    await act(async () => {
      await result.current.runEvaluation("gt", "cmp");
    });

    expect(result.current.evalError).toBe("Evaluation failed.");
  });

  it("clears the previous result and error when running again", async () => {
    evaluateAI.mockResolvedValueOnce({ ok: 1 });
    const { result } = renderHook(() => useEvaluation());
    await act(async () => {
      await result.current.runEvaluation("gt", "cmp");
    });
    expect(result.current.evalResult).toEqual({ ok: 1 });

    evaluateAI.mockRejectedValueOnce(new Error("second failed"));
    await act(async () => {
      await result.current.runEvaluation("gt", "cmp");
    });

    expect(result.current.evalResult).toBeNull();
    expect(result.current.evalError).toBe("second failed");

    evaluateAI.mockResolvedValueOnce({ ok: 2 });
    await act(async () => {
      await result.current.runEvaluation("gt", "cmp");
    });

    expect(result.current.evalError).toBe("");
    expect(result.current.evalResult).toEqual({ ok: 2 });
  });
});
