// src/hooks/StartPrelabellingPage/usePrelabelJob.polling.test.js
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePrelabelJob } from "./usePrelabelJob.js";
import { getPrelabelStatus } from "../../api/StartPrelabellingPage/api.js";

vi.mock("../../api/StartPrelabellingPage/api.js");

const advance = (ms) =>
  act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });

describe("usePrelabelJob polling", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetAllMocks();
    vi.useFakeTimers();
    localStorage.setItem("prelabelJobId", "job-1");
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("does not poll without a job id", async () => {
    localStorage.clear();

    renderHook(() => usePrelabelJob());
    await advance(5000);

    expect(getPrelabelStatus).not.toHaveBeenCalled();
  });

  it("polls immediately and then again after 1500 ms while the job runs", async () => {
    getPrelabelStatus.mockResolvedValue({ state: "RUNNING", progress: 10 });

    renderHook(() => usePrelabelJob());
    await advance(0);
    expect(getPrelabelStatus).toHaveBeenCalledTimes(1);

    await advance(1500);
    expect(getPrelabelStatus).toHaveBeenCalledTimes(2);
  });

  it("stops polling after unmount", async () => {
    getPrelabelStatus.mockResolvedValue({ state: "RUNNING", progress: 10 });

    const { unmount } = renderHook(() => usePrelabelJob());
    await advance(0);
    unmount();
    await advance(5000);

    expect(getPrelabelStatus).toHaveBeenCalledTimes(1);
  });

  it("clears the job id, reports the outcome and stops polling when the job is done", async () => {
    getPrelabelStatus.mockResolvedValue({ state: "done", progress: 100 });

    const { result } = renderHook(() => usePrelabelJob());
    await advance(0);

    expect(result.current.preJobId).toBe("");
    expect(result.current.preStatus).toBeNull();
    expect(result.current.statusMsg).toBe("Prelabeling finished successfully.");

    await advance(5000);
    expect(getPrelabelStatus).toHaveBeenCalledTimes(1);
  });

  it("finishes a job whose cancel request reached 100 percent", async () => {
    getPrelabelStatus.mockResolvedValue({ state: "cancel_requested", progress: 100 });

    const { result } = renderHook(() => usePrelabelJob());
    await advance(0);

    expect(result.current.preJobId).toBe("");
    expect(result.current.statusMsg).toBe("Job finished (cancel request acknowledged).");
  });

  it("drops the job without a message when the backend answers 404", async () => {
    getPrelabelStatus.mockRejectedValue({ status: 404 });

    const { result } = renderHook(() => usePrelabelJob());
    await advance(0);

    expect(result.current.preJobId).toBe("");
    expect(result.current.statusMsg).toBe("");

    await advance(5000);
    expect(getPrelabelStatus).toHaveBeenCalledTimes(1);
  });

  it("drops the job without a message when the backend reports NOT_FOUND", async () => {
    getPrelabelStatus.mockResolvedValue({ job_id: "job-1", state: "NOT_FOUND" });

    const { result } = renderHook(() => usePrelabelJob());
    await advance(0);

    expect(result.current.preJobId).toBe("");
    expect(result.current.preStatus).toBeNull();
    expect(result.current.statusMsg).toBe("");

    await advance(5000);
    expect(getPrelabelStatus).toHaveBeenCalledTimes(1);
  });

  it("keeps the job id and polls again after another error", async () => {
    getPrelabelStatus.mockRejectedValueOnce(new Error("network"));
    getPrelabelStatus.mockResolvedValue({ state: "RUNNING", progress: 10 });

    const { result } = renderHook(() => usePrelabelJob());
    await advance(0);
    expect(result.current.preJobId).toBe("job-1");

    await advance(1500);
    expect(getPrelabelStatus).toHaveBeenCalledTimes(2);
    expect(result.current.preStatus).toEqual({ state: "RUNNING", progress: 10 });
  });
});
