// frontend/src/api/EvaluateAIPage/api.test.js
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  getProjectsReadyForGroundtruth,
  saveAsGtSet,
  getProjectsReadyForComparison,
  getGroundtruthProjectsForComparison,
  evaluateAI,
} from "./api.js";

function jsonResponse(data) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    json: async () => data,
  };
}

describe("EvaluateAIPage api", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("getProjectsReadyForGroundtruth GETs /list-projects-ready-for-groundtruth and returns the projects", async () => {
    fetch.mockResolvedValue(jsonResponse({ projects: ["a", "b"] }));

    const projects = await getProjectsReadyForGroundtruth();

    const [url, opts] = fetch.mock.calls[0];
    expect(url).toMatch(/\/list-projects-ready-for-groundtruth$/);
    expect(opts.method).toBe("GET");
    expect(projects).toEqual(["a", "b"]);
  });

  it("getProjectsReadyForGroundtruth returns an empty list when projects is not an array", async () => {
    fetch.mockResolvedValue(jsonResponse({ projects: "nope" }));

    expect(await getProjectsReadyForGroundtruth()).toEqual([]);
  });

  it("saveAsGtSet posts source_project and scope with the bearer token", async () => {
    fetch.mockResolvedValue(jsonResponse({ status: "ok" }));

    const result = await saveAsGtSet("tok", "my-project", "internal");

    const [url, opts] = fetch.mock.calls[0];
    expect(url).toMatch(/\/save-as-gt-set$/);
    expect(opts.method).toBe("POST");
    expect(opts.headers).toEqual({
      "Content-Type": "application/json",
      Authorization: "Bearer tok",
    });
    expect(JSON.parse(opts.body)).toEqual({ source_project: "my-project", scope: "internal" });
    expect(result).toEqual({ status: "ok" });
  });

  it("getProjectsReadyForComparison GETs /list-projects-ready-for-comparison and returns the projects", async () => {
    fetch.mockResolvedValue(jsonResponse({ projects: ["a"] }));

    const projects = await getProjectsReadyForComparison();

    const [url, opts] = fetch.mock.calls[0];
    expect(url).toMatch(/\/list-projects-ready-for-comparison$/);
    expect(opts.method).toBe("GET");
    expect(projects).toEqual(["a"]);
  });

  it("getProjectsReadyForComparison returns an empty list when projects is missing", async () => {
    fetch.mockResolvedValue(jsonResponse({}));

    expect(await getProjectsReadyForComparison()).toEqual([]);
  });

  it("getGroundtruthProjectsForComparison posts comparison_project and returns the projects", async () => {
    fetch.mockResolvedValue(jsonResponse({ projects: ["gt1", "gt2"] }));

    const projects = await getGroundtruthProjectsForComparison("cmp");

    const [url, opts] = fetch.mock.calls[0];
    expect(url).toMatch(/\/list-groundtruth-projects-for-comparison$/);
    expect(opts.method).toBe("POST");
    expect(opts.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(opts.body)).toEqual({ comparison_project: "cmp" });
    expect(projects).toEqual(["gt1", "gt2"]);
  });

  it("getGroundtruthProjectsForComparison returns an empty list when projects is not an array", async () => {
    fetch.mockResolvedValue(jsonResponse({ projects: null }));

    expect(await getGroundtruthProjectsForComparison("cmp")).toEqual([]);
  });

  it("evaluateAI posts both project names without an Authorization header", async () => {
    const data = { metrics: {} };
    fetch.mockResolvedValue(jsonResponse(data));

    const result = await evaluateAI("gt", "cmp");

    const [url, opts] = fetch.mock.calls[0];
    expect(url).toMatch(/\/evaluate-ai$/);
    expect(opts.method).toBe("POST");
    expect(opts.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(opts.body)).toEqual({
      groundtruth_project: "gt",
      comparison_project: "cmp",
    });
    expect(result).toEqual(data);
  });
});
