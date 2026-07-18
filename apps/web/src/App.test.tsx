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
      if (url.includes("/technology/learning/curriculum/gaps")) {
        return jsonResponse({
          gaps: [
            {
              gap_id: "gap_1",
              domain: "Frontend",
              topic: "React",
              subtopic: "Hooks",
              signals: ["missing_verified_questions"],
              severity: 0.7,
              recommended_action: "generate_reviewable_questions",
            },
          ],
        });
      }
      if (url.includes("/technology/learning/curriculum")) {
        return jsonResponse({
          curriculum_id: "technology-student-v0.1",
          overall_coverage_score: 0.42,
          insufficient_topics: ["react-hooks"],
          topic_scores: [
            {
              topic_id: "react-hooks",
              domain: "Frontend",
              topic: "React",
              subtopic: "Hooks",
              current_coverage_score: 0.42,
              current_quality_score: 0.2,
              approved_source_count: 1,
              ingested_document_count: 1,
              verified_question_count: 0,
              evaluation_example_count: 0,
              known_knowledge_gaps: [],
              next_recommended_learning_action: "generate_reviewable_questions",
            },
          ],
        });
      }
      if (url.includes("/technology/learning/cycles")) {
        return jsonResponse({
          cycles: [
            {
              cycle_id: "cycle_1",
              domain: "Frontend",
              topic: "React",
              objectives: ["Explain hooks"],
              maximum_examples: 2,
              status: "planned",
              metrics: {},
            },
          ],
        });
      }
      if (init?.method === "POST" && url.includes("/technology/learning/reviews/review_1/approve")) {
        return jsonResponse({
          review_id: "review_1",
          candidate_id: "cand_1",
          question_id: "q_1",
          status: "approved",
          reviewer_id: "reviewer_1",
          reviewer_note: "Approved by authenticated reviewer.",
        });
      }
      if (url.includes("/technology/learning/reviews")) {
        return jsonResponse({
          reviews: [
            {
              review_id: "review_1",
              candidate_id: "cand_1",
              question_id: "q_1",
              status: "pending",
              reviewer_id: null,
              reviewer_note: null,
            },
          ],
        });
      }
      if (url.includes("/technology/learning/dataset-candidates")) {
        return jsonResponse({
          dataset_candidates: [
            {
              dataset_candidate_id: "dsc_1",
              dataset_type: "sft",
              status: "pending",
              record_ids: ["record_1"],
            },
          ],
        });
      }
      if (url.includes("/technology/learning/dataset-versions")) {
        return jsonResponse({
          dataset_versions: [
            {
              dataset_version_id: "dsv_1",
              name: "Technology SFT v0.1",
              dataset_type: "sft",
              approved_record_count: 1,
              approval_status: "approved",
              content_manifest_hash: "abc123",
            },
          ],
        });
      }
      if (url.includes("/technology/learning/model-candidates")) {
        return jsonResponse({
          model_candidates: [
            {
              candidate_id: "model_1",
              base_model: "local-base",
              dataset_version: "dsv_1",
              approval_state: "pending",
              deployment_recommendation: "not_recommended",
            },
          ],
        });
      }
      if (url.includes("/technology/training/hardware")) {
        return jsonResponse({
          status: "available",
          report: {
            report_id: "hw_1",
            operating_system: "Windows",
            python_version: "3.12.13",
            cpu: "test-cpu",
            system_ram_gb: 16,
            gpu_available: false,
            gpu_name: null,
            gpu_memory_gb: null,
            cuda_available: false,
            available_disk_gb: 100,
            recommended_training_mode: "cpu_only_smoke_test",
            expected_limitations: ["CUDA GPU unavailable; real LoRA training may be slow or unavailable."],
          },
        });
      }
      if (url.includes("/technology/training/base-models")) {
        return jsonResponse({
          base_model_manifests: [
            {
              manifest_id: "base_1",
              model_identifier: "local/open-weight-test",
              exact_revision: "0123456789abcdef",
              license_name: "Apache-2.0",
              fine_tuning_permission: "allowed",
              required_trust_remote_code: false,
              human_license_review_status: "approved",
              approval_status: "approved",
            },
          ],
        });
      }
      if (url.includes("/technology/training/datasets/dsv_1/validation-report")) {
        return jsonResponse({
          report_id: "report_1",
          dataset_version_id: "dsv_1",
          valid: true,
          approved_record_count: 1,
          training_count: 1,
          validation_count: 0,
          held_out_test_count: 0,
          secret_scan_result: "passed",
          blocking_issues: [],
        });
      }
      if (url.includes("/technology/training/runs")) {
        return jsonResponse({
          training_runs: [
            {
              run_id: "run_1",
              experiment_name: "phase3-smoke",
              status: "completed",
              base_model_identifier: "local/open-weight-test",
              dataset_version: "dsv_1",
              current_step: 1,
              adapter_location: "storage/generated/training/run_1/adapter.safetensors",
              adapter_hash: "hash123",
              metrics_location: "storage/generated/training/run_1/metrics.json",
              safe_error_summary: null,
            },
          ],
        });
      }
      if (url.includes("/technology/training/candidates")) {
        return jsonResponse({
          model_candidates: [
            {
              candidate_id: "candidate_1",
              candidate_name: "Technology Student v0.1 Candidate",
              base_model_manifest_id: "base_1",
              dataset_version: "dsv_1",
              approval_state: "pending",
              deployment_recommendation: "needs_more_evaluation",
              safety_status: "passed",
              license_status: "approved",
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

  it("shows Phase 2 curriculum dashboard", async () => {
    render(<App />);

    await userEvent.click(screen.getByRole("button", { name: "learning" }));

    expect(await screen.findByText("Curriculum Dashboard")).toBeInTheDocument();
    expect(screen.getAllByText("42%")).toHaveLength(2);
    expect(screen.getByText("generate_reviewable_questions")).toBeInTheDocument();
  });

  it("shows learning cycles", async () => {
    render(<App />);

    await userEvent.click(screen.getByRole("button", { name: "cycles" }));

    expect(await screen.findByText("Learning Cycles")).toBeInTheDocument();
    expect(screen.getByText("Maximum examples: 2")).toBeInTheDocument();
  });

  it("shows and approves a review item", async () => {
    render(<App />);

    await userEvent.click(screen.getByRole("button", { name: "review" }));
    await userEvent.click(await screen.findByRole("button", { name: "Approve" }));

    expect(await screen.findByText("approved")).toBeInTheDocument();
  });

  it("shows dataset and model registries", async () => {
    render(<App />);

    await userEvent.click(screen.getByRole("button", { name: "datasets" }));
    expect(await screen.findByText("Technology SFT v0.1")).toBeInTheDocument();
    expect(screen.getByText("Manifest: abc123")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "models" }));
    expect(await screen.findByText("local-base")).toBeInTheDocument();
    expect(screen.getByText("Recommendation: not_recommended")).toBeInTheDocument();
  });

  it("shows Phase 3 training administration views", async () => {
    render(<App />);

    await userEvent.click(screen.getByRole("button", { name: "hardware" }));
    expect(await screen.findByText("Hardware Assessment")).toBeInTheDocument();
    expect(screen.getByText("cpu_only_smoke_test")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "base" }));
    expect(await screen.findByText("local/open-weight-test")).toBeInTheDocument();
    expect(screen.getByText("License: Apache-2.0")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "train-data" }));
    expect(await screen.findByText("Latest Validation")).toBeInTheDocument();
    expect(screen.getByText("Secret scan: passed")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "runs" }));
    expect(await screen.findByText("phase3-smoke")).toBeInTheDocument();
    expect(screen.getByText("Adapter hash: hash123")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "candidates" }));
    expect(await screen.findByText("Technology Student v0.1 Candidate")).toBeInTheDocument();
    expect(screen.getByText("Recommendation: needs_more_evaluation")).toBeInTheDocument();
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
