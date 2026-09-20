// src/hooks/PDFUploadAndConversionPage/useJobManager.test.js
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import useJobManager from "./useJobManager.js";
import { prepareConversion } from "../../api/PDFUploadAndConversionPage/api.js";

vi.mock("../../api/PDFUploadAndConversionPage/api.js");

describe("useJobManager handleSubmit guard", () => {
  beforeEach(() => {
    localStorage.clear();
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
});