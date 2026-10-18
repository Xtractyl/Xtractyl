// frontend/src/api/GetResultsPage/api.test.js  (neu)
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getProjectsReadyForResults, getResultsTable } from "./api.js";

function jsonResponse(data) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    json: async () => data,
  };
}

describe("GetResultsPage api", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("getProjectsReadyForResults GETs /list_projects_ready_for_results and returns the projects", async () => {
    fetch.mockResolvedValue(jsonResponse({ projects: ["a", "b"] }));

    const projects = await getProjectsReadyForResults();

    const [url, opts] = fetch.mock.calls[0];
    expect(url).toMatch(/\/list_projects_ready_for_results$/);
    expect(opts.method).toBe("GET");
    expect(projects).toEqual(["a", "b"]);
  });

  it("getResultsTable posts project_name as JSON to /results/table", async () => {
    fetch.mockResolvedValue(jsonResponse({ columns: [], rows: [], total: 0 }));

    await getResultsTable({ projectName: "my-project" });

    const [url, opts] = fetch.mock.calls[0];
    expect(url).toMatch(/\/results\/table$/);
    expect(opts.method).toBe("POST");
    expect(opts.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(opts.body)).toEqual({ project_name: "my-project" });
  });

  it("getResultsTable returns columns, rows and total from the response", async () => {
    const data = {
      columns: ["task_id", "filename"],
      rows: [{ task_id: 1, filename: "a.html" }],
      total: 1,
    };
    fetch.mockResolvedValue(jsonResponse(data));

    const result = await getResultsTable({ projectName: "p" });

    expect(result).toEqual(data);
  });

  it("getResultsTable falls back to empty defaults for missing or malformed fields", async () => {
    fetch.mockResolvedValue(jsonResponse({ columns: "nope", rows: null, total: "3" }));

    const result = await getResultsTable({ projectName: "p" });

    expect(result).toEqual({ columns: [], rows: [], total: 0 });
  });
});
