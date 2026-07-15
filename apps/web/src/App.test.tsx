import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const healthyResponses = [
  {
    service: "devmind-api",
    status: "healthy",
    version: "0.1.0",
  },
  {
    service: "devmind-api",
    status: "ready",
    version: "0.1.0",
    checks: {
      api: { available: true, detail: "process available" },
      configuration: { available: true, detail: "required configuration present" },
      mongodb: { available: true, detail: "ping succeeded" },
    },
  },
];

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() => {
        const next = healthyResponses.shift();
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(next),
        });
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    healthyResponses.splice(0, healthyResponses.length, {
      service: "devmind-api",
      status: "healthy",
      version: "0.1.0",
    }, {
      service: "devmind-api",
      status: "ready",
      version: "0.1.0",
      checks: {
        api: { available: true, detail: "process available" },
        configuration: { available: true, detail: "required configuration present" },
        mongodb: { available: true, detail: "ping succeeded" },
      },
    });
  });

  it("shows a loading state", () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(() => new Promise(() => undefined)));

    render(<App />);

    expect(screen.getByLabelText("Loading status")).toBeInTheDocument();
  });

  it("shows healthy status", async () => {
    render(<App />);

    await waitFor(() => expect(screen.getByText("devmind-api 0.1.0")).toBeInTheDocument());
    expect(screen.getByText("ping succeeded")).toBeInTheDocument();
    expect(screen.getByText("available")).toBeInTheDocument();
  });

  it("shows unavailable status", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    render(<App />);

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByText("The API status endpoint could not be reached.")).toBeInTheDocument();
  });
});
