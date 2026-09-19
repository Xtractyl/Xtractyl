// src/pages/UploadTasks.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppProvider } from "../context/AppContext";
import UploadTasksPage from "./UploadTasks.jsx";

describe("UploadTasks page", () => {
  it("renders the upload tasks heading", () => {
    render(
      <AppProvider>
        <UploadTasksPage />
      </AppProvider>
    );

    expect(screen.getByText("Upload Tasks")).toBeInTheDocument();
  });
});