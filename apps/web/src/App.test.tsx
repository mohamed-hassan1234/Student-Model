import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

function jsonResponse(payload: unknown, ok = true) {
  return Promise.resolve({ ok, json: () => Promise.resolve(payload) });
}

function installFetchMock() {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "POST" && url.includes("/student/ask")) {
        return jsonResponse({
          answer: "I do not have enough approved evidence to answer that as a verified fact.",
          confidence: 0,
          topic: null,
          evidence_status: "insufficient_evidence",
          limitations: ["No sufficiently relevant approved chunks were retrieved."],
          sources: [],
        });
      }
      if (url.includes("/health")) {
        return jsonResponse({ service: "devmind-api", status: "healthy", version: "0.1.0" });
      }
      if (url.includes("/ready")) {
        return jsonResponse({
          service: "devmind-api",
          status: "ready",
          version: "0.1.0",
          checks: {
            api: { available: true, detail: "process available" },
            configuration: { available: true, detail: "required configuration present" },
            mongodb: { available: true, detail: "ping succeeded" },
          },
        });
      }
      if (url.includes("/sources")) {
        return jsonResponse({
          sources: [
            {
              source_id: "src_1",
              name: "React docs",
              description: "Approved React docs",
              source_status: "approved",
              ingestion_status: "completed",
              trust_level: "official",
              license_type: "mit",
              retrieval_use_permission: "allowed",
              training_use_permission: "disallowed",
              technology_topic: "react",
            },
          ],
        });
      }
      if (url.includes("/curriculum")) {
        return jsonResponse({
          topics: [
            {
              topic: "react",
              available_source_count: 1,
              ingested_document_count: 1,
              coverage: "partial",
            },
          ],
        });
      }
      return jsonResponse({}, false);
    }),
  );
}

describe("App", () => {
  beforeEach(() => {
    installFetchMock();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
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

  it("shows registered sources", async () => {
    render(<App />);

    await userEvent.click(screen.getByRole("button", { name: "sources" }));

    expect(await screen.findByText("React docs")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
  });

  it("shows curriculum coverage", async () => {
    render(<App />);

    await userEvent.click(screen.getByRole("button", { name: "curriculum" }));

    expect(await screen.findByText("react")).toBeInTheDocument();
    expect(screen.getByText("Coverage: partial")).toBeInTheDocument();
  });

  it("shows insufficient-evidence chat response", async () => {
    render(<App />);

    await userEvent.click(screen.getByRole("button", { name: "student" }));
    await userEvent.type(screen.getByLabelText("Question"), "What is Rust?");
    await userEvent.click(screen.getByRole("button", { name: "Ask" }));

    expect(await screen.findByText("insufficient_evidence")).toBeInTheDocument();
    expect(screen.getByText("No citations available.")).toBeInTheDocument();
  });
});
