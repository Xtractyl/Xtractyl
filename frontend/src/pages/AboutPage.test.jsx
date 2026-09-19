// src/pages/AboutPage.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import AboutPage from "./AboutPage.jsx";

describe("AboutPage", () => {
  it("renders the about heading", () => {
    render(<AboutPage />);

    expect(screen.getByText("About Xtractyl")).toBeInTheDocument();
  });
});