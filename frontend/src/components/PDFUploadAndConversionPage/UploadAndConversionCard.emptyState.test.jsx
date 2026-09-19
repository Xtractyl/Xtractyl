// src/components/PDFUploadAndConversionPage/UploadAndConversionCard.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppProvider } from "../../context/AppContext";
import UploadAndConversionCard from "./UploadAndConversionCard.jsx";

describe("UploadAndConversionCard", () => {
  it("renders the empty form with no active job", () => {
    render(
      <AppProvider>
        <UploadAndConversionCard />
      </AppProvider>
    );

    // Heading and description
    expect(screen.getByText("Upload and Convert Docs")).toBeInTheDocument();
    expect(
      screen.getByText("Enter a project name and select PDFs to convert.")
    ).toBeInTheDocument();

    // Inputs found via their linked labels
    expect(screen.getByLabelText("Project name")).toBeInTheDocument();
    expect(screen.getByLabelText("Select your PDFs")).toHaveAttribute(
      "accept",
      "application/pdf"
    );

    // No files selected yet
    expect(screen.queryByText(/file\(s\) selected/)).not.toBeInTheDocument();

    // Submit button present, enabled, default label
    const submitButton = screen.getByRole("button", { name: "Upload & Convert" });
    expect(submitButton).toBeEnabled();

    // No job yet -> neither status panel nor active job controls should render
    expect(screen.queryByText(/^Status:/)).not.toBeInTheDocument();
    expect(screen.queryByText("Active conversion job")).not.toBeInTheDocument();
  });
});