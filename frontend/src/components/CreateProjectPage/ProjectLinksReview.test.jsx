// frontend/src/components/CreateProjectPage/ProjectLinksReview.test.jsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import ProjectLinksReview from "./ProjectLinksReview.jsx";

const links = { comparison: ["projA", "projB"], regression: ["projA"], drift: [] };

function renderReview(props = {}) {
  const handlers = { onConfirm: vi.fn(), onEdit: vi.fn(), onCancel: vi.fn() };
  render(<ProjectLinksReview links={links} busy={false} {...handlers} {...props} />);
  return handlers;
}

describe("ProjectLinksReview", () => {
  it("lists the matching projects in the section they belong to", () => {
    renderReview();

    const comparison = within(screen.getByRole("region", { name: "Comparison" }));
    expect(comparison.getByText("projA")).toBeInTheDocument();
    expect(comparison.getByText("projB")).toBeInTheDocument();

    const regression = within(screen.getByRole("region", { name: "Regression" }));
    expect(regression.getByText("projA")).toBeInTheDocument();
    expect(regression.queryByText("projB")).not.toBeInTheDocument();
  });

  it("says so when a section has no matching project", () => {
    renderReview();

    const drift = within(screen.getByRole("region", { name: "Drift" }));
    expect(drift.getByText("No matching projects.")).toBeInTheDocument();
  });

  it("always warns that a link needs the whole set to match", () => {
    renderReview({ links: { comparison: [], regression: [], drift: [] } });

    expect(
      screen.getByText(/Links are only created when the whole set matches/)
    ).toBeInTheDocument();
  });

  it("calls the matching handler for each button", () => {
    const { onConfirm, onEdit, onCancel } = renderReview();

    fireEvent.click(screen.getByRole("button", { name: "Confirm and create project" }));
    fireEvent.click(screen.getByRole("button", { name: "Back to edit" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancel and delete project" }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onEdit).toHaveBeenCalledTimes(1);
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("disables all buttons while busy", () => {
    renderReview({ busy: true });

    expect(screen.getByRole("button", { name: "Confirm and create project" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Back to edit" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel and delete project" })).toBeDisabled();
  });
});
