// src/hooks/StartPrelabellingPage/usePrelabelJob.startAndCancel.test.js
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { usePrelabelJob } from "./usePrelabelJob.js";
import {
  prelabelProject,
  cancelPrelabel,
  getPrelabelStatus,
} from "../../api/StartPrelabellingPage/api.js";

vi.mock("../../api/StartPrelabellingPage/api.js");

describe("usePrelabelJob start", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetAllMocks();
  });

  it("stores the job id and starts polling after a successful start", async () => {
    prelabelProject.mockResolvedValue({ job_id: "job-1" });
    getPrelabelStatus.mockResolvedValue({ state: "RUNNING", progress: 20 });

    const { result } = renderHook(() => usePrelabelJob());

    await act(async () => {
      await result.current.start({ project_name: "p", token: "t" });
    });

    expect(prelabelProject).toHaveBeenCalledWith({ project_name: "p", token: "t" });
    expect(result.current.preJobId).toBe("job-1");
    expect(localStorage.getItem("prelabelJobId")).toBe("job-1");
    expect(result.current.busy).toBe(false);
    expect(result.current.statusMsg).toBe("Prelabeling started.");
    await waitFor(() => expect(result.current.progressPct).toBe(20));
  });

  it("reports the error and keeps no job id when starting fails", async () => {
    prelabelProject.mockRejectedValue(new Error("boom"));

    const { result } = renderHook(() => usePrelabelJob());

    await act(async () => {
      await result.current.start({ project_name: "p", token: "t" });
    });

    expect(result.current.preJobId).toBe("");
    expect(result.current.busy).toBe(false);
    expect(result.current.statusMsg).toBe("boom");
    expect(getPrelabelStatus).not.toHaveBeenCalled();
  });
});

describe("usePrelabelJob cancel", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetAllMocks();
    localStorage.setItem("prelabelJobId", "job-1");
  });

  it("requests the cancel and shows the translated status", async () => {
    getPrelabelStatus.mockResolvedValueOnce({ state: "RUNNING", progress: 40 });
    getPrelabelStatus.mockResolvedValue({ state: "CANCEL_REQUESTED", progress: 40 });
    cancelPrelabel.mockResolvedValue({});

    const { result } = renderHook(() => usePrelabelJob());
    await waitFor(() => expect(result.current.preStatus).not.toBeNull());

    await act(async () => {
      await result.current.cancel();
    });

    expect(cancelPrelabel).toHaveBeenCalledWith("job-1");
    expect(result.current.statusMsg).toBe("Cancel requested.");
  });

  it("shows the error when the cancel request fails", async () => {
    getPrelabelStatus.mockResolvedValue({ state: "RUNNING", progress: 40 });
    cancelPrelabel.mockRejectedValue(new Error("nope"));

    const { result } = renderHook(() => usePrelabelJob());
    await waitFor(() => expect(result.current.preStatus).not.toBeNull());

    await act(async () => {
      await result.current.cancel();
    });

    expect(result.current.statusMsg).toBe("nope");
  });
});
