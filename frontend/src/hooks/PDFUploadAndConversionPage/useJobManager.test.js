// src/hooks/PDFUploadAndConversionPage/useJobManager.test.js
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import useJobManager from "./useJobManager.js";
import { prepareConversion, uploadToMinio, startConversion, discardConversion } from "../../api/PDFUploadAndConversionPage/api.js";

vi.mock("../../api/PDFUploadAndConversionPage/api.js");

describe("useJobManager handleSubmit guard", () => {
  
    beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not start a conversion when projectName is missing", async () => {
    const { result } = renderHook(() => useJobManager("", [{ name: "a.pdf" }]));

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(prepareConversion).not.toHaveBeenCalled();
  });

  it("does not start a conversion when no files are selected", async () => {
    const { result } = renderHook(() => useJobManager("my-project", []));

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(prepareConversion).not.toHaveBeenCalled();
  });

  it("uploads all files and starts conversion on a successful submit", async () => {
  const files = [{ name: "a.pdf" }, { name: "b.pdf" }];
  prepareConversion.mockResolvedValue({
    job_id: "job-1",
    presigned_urls: [
      { filename: "a.pdf", upload_url: "https://minio/a", pdf_key: "p/a.pdf" },
      { filename: "b.pdf", upload_url: "https://minio/b", pdf_key: "p/b.pdf" },
    ],
  });
  uploadToMinio.mockResolvedValue(undefined);
  startConversion.mockResolvedValue({ job_id: "job-1", status: "converting" });

  const { result } = renderHook(() => useJobManager("my-project", files));

  await act(async () => {
    await result.current.handleSubmit();
  });

  expect(prepareConversion).toHaveBeenCalledWith("my-project", ["a.pdf", "b.pdf"]);
  expect(uploadToMinio).toHaveBeenCalledTimes(2);
  expect(startConversion).toHaveBeenCalledWith("job-1");
  expect(result.current.jobId).toBe("job-1");
  expect(result.current.serverMsg).toBe("Upload complete, conversion started.");
  expect(discardConversion).not.toHaveBeenCalled();
});

it("discards the job when the upload fails after prepareConversion succeeded", async () => {
  const files = [{ name: "a.pdf" }];
  prepareConversion.mockResolvedValue({
    job_id: "job-2",
    presigned_urls: [{ filename: "a.pdf", upload_url: "https://minio/a", pdf_key: "p/a.pdf" }],
  });
  uploadToMinio.mockRejectedValue(new Error("network error"));
  discardConversion.mockResolvedValue({ status: "discarded" });

  const { result } = renderHook(() => useJobManager("my-project", files));

  await act(async () => {
    await result.current.handleSubmit();
  });

  expect(discardConversion).toHaveBeenCalledWith("job-2");
  expect(result.current.jobId).toBeNull();
  expect(result.current.serverMsg).toBe("network error");
});

it("does not call discardConversion when prepareConversion itself fails", async () => {
  const files = [{ name: "a.pdf" }];
  prepareConversion.mockRejectedValue(new Error("Project already exists"));

  const { result } = renderHook(() => useJobManager("my-project", files));

  await act(async () => {
    await result.current.handleSubmit();
  });

  expect(discardConversion).not.toHaveBeenCalled();
  expect(result.current.jobId).toBeNull();
  expect(result.current.serverMsg).toBe("Project already exists");
});
});