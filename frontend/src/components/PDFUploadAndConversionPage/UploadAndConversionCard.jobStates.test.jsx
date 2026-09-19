// src/components/PDFUploadAndConversionPage/UploadAndConversionCard.jobStates.test.jsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppProvider } from "../../context/AppContext.jsx";
import UploadAndConversionCard from "./UploadAndConversionCard.jsx";
import { getConversionStatus , discardConversion } from "../../api/PDFUploadAndConversionPage/api.js";

vi.mock("../../api/PDFUploadAndConversionPage/api.js");

describe("UploadAndConversionCard with an existing job", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

      it("shows the status panel but no cancel button while pending", async () => {
    localStorage.setItem("conversionJobId", "job-456");
    getConversionStatus.mockResolvedValue({
      job_id: "job-456",
      status: "pending",
      total_files: 0,
      converted_files: 0,
    });

    render(
      <AppProvider>
        <UploadAndConversionCard />
      </AppProvider>
    );

    expect(await screen.findByText(/Status: pending/)).toBeInTheDocument();

    expect(
      screen.queryByRole("button", { name: "Cancel and Delete Project" })
    ).not.toBeInTheDocument();
  });

    it("shows the status panel and the cancel button while converting", async () => {
    localStorage.setItem("conversionJobId", "job-123");
    getConversionStatus.mockResolvedValue({
      job_id: "job-123",
      status: "converting",
      total_files: 4,
      converted_files: 1,
    });

    render(
      <AppProvider>
        <UploadAndConversionCard />
      </AppProvider>
    );

    
    expect(
      await screen.findByText(/Status: converting/)
    ).toBeInTheDocument();
    expect(screen.getByText("1/4 files", { exact: false })).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Cancel and Delete Project" })
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Job running…" })
    ).toBeDisabled();

  
  });
    it("shows the error message and discards the job when conversion fails", async () => {
    localStorage.setItem("conversionJobId", "job-999");
    getConversionStatus.mockResolvedValue({
      job_id: "job-999",
      status: "failed",
      total_files: 3,
      converted_files: 1,
      error: "Docling timed out",
    });
    discardConversion.mockResolvedValue({ status: "discarded" });

    render(
      <AppProvider>
        <UploadAndConversionCard />
      </AppProvider>
    );

    expect(
      await screen.findByText("❌ Conversion failed. Docling timed out")
    ).toBeInTheDocument();
    expect(discardConversion).toHaveBeenCalledWith("job-999");
  });

  it("shows the cancelled message and discards the job when cancelled", async () => {
    localStorage.setItem("conversionJobId", "job-000");
    getConversionStatus.mockResolvedValue({
      job_id: "job-000",
      status: "cancelled",
      total_files: 3,
      converted_files: 1,
    });
    discardConversion.mockResolvedValue({ status: "discarded" });

    render(
      <AppProvider>
        <UploadAndConversionCard />
      </AppProvider>
    );

    expect(
      await screen.findByText("⏹️ Conversion cancelled.")
    ).toBeInTheDocument();
    expect(discardConversion).toHaveBeenCalledWith("job-000");
  });
});