// src/pages/PDFUploadAndConversion.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppProvider } from "../context/AppContext";
import PDFUploadAndConversion from "./PDFUploadandConversion.jsx";

describe("PDFUploadAndConversion page", () => {
  it("renders the upload form", () => {
    render(
      <AppProvider>
        <PDFUploadAndConversion />
      </AppProvider>
    );

    expect(
      screen.getByText("Upload and Convert Docs")
    ).toBeInTheDocument();
  });
});