// src/api/PDFUploadAndConversionPage/api.test.js
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  prepareConversion,
  getConversionStatus,
  uploadToMinio,
} from "./api.js";

function okResponse() {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    json: async () => ({}),
  };
}

describe("PDFUploadAndConversionPage api", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okResponse()));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("prepareConversion posts the project name and filenames to /conversion/prepare", async () => {
    await prepareConversion("my-project", ["a.pdf", "b.pdf"]);

    const [url, opts] = fetch.mock.calls[0];
    expect(url).toMatch(/\/conversion\/prepare$/);
    expect(opts.method).toBe("POST");
    expect(JSON.parse(opts.body)).toEqual({
      project: "my-project",
      filenames: ["a.pdf", "b.pdf"],
    });
  });

  it("getConversionStatus GETs /conversion/status/:jobId", async () => {
    await getConversionStatus("job-1");

    const [url, opts] = fetch.mock.calls[0];
    expect(url).toMatch(/\/conversion\/status\/job-1$/);
    expect(opts.method).toBe("GET");
  });

  it("uploadToMinio PUTs the file to the given URL", async () => {
    const fakeFile = new Blob(["content"], { type: "application/pdf" });

    await uploadToMinio("https://minio.example/upload-url", fakeFile);

    const [url, opts] = fetch.mock.calls[0];
    expect(url).toBe("https://minio.example/upload-url");
    expect(opts.method).toBe("PUT");
    expect(opts.body).toBe(fakeFile);
  });

  it("uploadToMinio throws with the file name and status on failure", async () => {
    fetch.mockResolvedValue({ ok: false, status: 500 });
    const fakeFile = new Blob(["content"], { type: "application/pdf" });
    Object.defineProperty(fakeFile, "name", { value: "broken.pdf" });

    await expect(
      uploadToMinio("https://minio.example/upload-url", fakeFile)
    ).rejects.toMatchObject({ message: "MinIO upload failed for broken.pdf: 500", status: 500 });
  });
});