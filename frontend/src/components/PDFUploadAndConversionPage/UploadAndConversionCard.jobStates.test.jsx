// src/components/PDFUploadAndConversionPage/UploadAndConversionCard.jobStates.test.jsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppProvider } from "../../context/AppContext";
import UploadAndConversionCard from "./UploadAndConversionCard.jsx";
import { getConversionStatus } from "../../api/PDFUploadAndConversionPage/api.js";

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
});