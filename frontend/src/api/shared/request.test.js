// frontend/src/api/shared/request.test.js
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { request } from "./request";

const BASE = "http://example.test";

function makeResponse({
  ok = true,
  status = 200,
  contentType = "application/json",
  json = async () => ({}),
  text = async () => "",
} = {}) {
  return { ok, status, headers: { get: () => contentType }, json, text };
}

describe("request", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("calls fetch with base url + path and defaults to GET", async () => {
    fetch.mockResolvedValue(makeResponse({ json: async () => ({ a: 1 }) }));

    const data = await request(BASE, "/path");

    const [url, opts] = fetch.mock.calls[0];
    expect(url).toBe("http://example.test/path");
    expect(opts.method).toBe("GET");
    expect(data).toEqual({ a: 1 });
  });

  it("passes method, headers and body through", async () => {
    fetch.mockResolvedValue(makeResponse());

    await request(BASE, "/p", {
      method: "POST",
      headers: { "X-Test": "1" },
      body: "payload",
    });

    const [, opts] = fetch.mock.calls[0];
    expect(opts.method).toBe("POST");
    expect(opts.headers).toEqual({ "X-Test": "1" });
    expect(opts.body).toBe("payload");
  });

  it("returns null for 204 responses", async () => {
    fetch.mockResolvedValue(makeResponse({ status: 204 }));

    expect(await request(BASE, "/p")).toBeNull();
  });

  it("returns the text for non-JSON responses", async () => {
    fetch.mockResolvedValue(
      makeResponse({ contentType: "text/plain", text: async () => "plain body" })
    );

    expect(await request(BASE, "/p")).toBe("plain body");
  });

  it("throws an error with the message from the body, plus status and data", async () => {
    const body = { error: "SOME_CODE", message: "Readable explanation." };
    fetch.mockResolvedValue(makeResponse({ ok: false, status: 404, json: async () => body }));

    await expect(request(BASE, "/p")).rejects.toMatchObject({
      message: "Readable explanation.",
      status: 404,
      data: body,
    });
  });

  it("falls back to the error code when the body has no message", async () => {
    fetch.mockResolvedValue(
      makeResponse({ ok: false, status: 409, json: async () => ({ error: "SOME_CODE" }) })
    );

    await expect(request(BASE, "/p")).rejects.toMatchObject({ message: "SOME_CODE", status: 409 });
  });

  it("falls back to the HTTP status when the JSON body has neither message nor error", async () => {
    fetch.mockResolvedValue(makeResponse({ ok: false, status: 500, json: async () => ({}) }));

    await expect(request(BASE, "/p")).rejects.toMatchObject({ message: "HTTP 500", status: 500 });
  });

  it("falls back to the HTTP status when the error body is not JSON", async () => {
    fetch.mockResolvedValue(
      makeResponse({
        ok: false,
        status: 502,
        contentType: "text/html",
        text: async () => "<html>Bad gateway</html>",
      })
    );

    await expect(request(BASE, "/p")).rejects.toMatchObject({ message: "HTTP 502", status: 502 });
  });

  it("falls back to the HTTP status when the error body is invalid JSON", async () => {
    fetch.mockResolvedValue(
      makeResponse({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error("bad json");
        },
      })
    );

    await expect(request(BASE, "/p")).rejects.toMatchObject({ message: "HTTP 500" });
  });

  it("turns an aborted request into a timeout error", async () => {
    vi.useFakeTimers();
    fetch.mockImplementation(
      (_url, { signal }) =>
        new Promise((_resolve, reject) => {
          signal.addEventListener("abort", () =>
            reject(Object.assign(new Error("aborted"), { name: "AbortError" }))
          );
        })
    );

    const promise = request(BASE, "/p", { timeoutMs: 100 });
    const assertion = expect(promise).rejects.toMatchObject({
      message: "Request timeout",
      status: 0,
    });
    await vi.advanceTimersByTimeAsync(100);

    await assertion;
  });

  it("rethrows other network errors unchanged", async () => {
    const networkError = new Error("Failed to fetch");
    fetch.mockRejectedValue(networkError);

    await expect(request(BASE, "/p")).rejects.toBe(networkError);
  });
});
