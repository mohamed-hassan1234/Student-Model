export type ReadinessCheck = {
  available: boolean;
  detail: string;
};

export type HealthResponse = {
  service: string;
  status: "healthy";
  version: string;
};

export type ReadinessResponse = {
  service: string;
  status: "ready" | "not_ready";
  version: string;
  checks: Record<string, ReadinessCheck>;
};

export type SystemStatus = {
  health: HealthResponse;
  readiness: ReadinessResponse;
};

export type Source = {
  source_id: string;
  name: string;
  description: string;
  source_status: string;
  ingestion_status: string;
  trust_level: string;
  license_type: string;
  retrieval_use_permission: string;
  training_use_permission: string;
  technology_topic: string;
};

export type CurriculumTopic = {
  topic: string;
  available_source_count: number;
  ingested_document_count: number;
  coverage: string;
};

export type LearningCurriculumTopic = {
  topic_id: string;
  domain: string;
  topic: string;
  subtopic: string | null;
  current_coverage_score: number;
  current_quality_score: number;
  approved_source_count: number;
  ingested_document_count: number;
  verified_question_count: number;
  evaluation_example_count: number;
  known_knowledge_gaps: string[];
  next_recommended_learning_action: string;
};

export type CoverageReport = {
  curriculum_id: string;
  overall_coverage_score: number;
  topic_scores: LearningCurriculumTopic[];
  insufficient_topics: string[];
};

export type KnowledgeGap = {
  gap_id: string;
  domain: string;
  topic: string;
  subtopic: string | null;
  signals: string[];
  severity: number;
  recommended_action: string;
};

export type LearningCycle = {
  cycle_id: string;
  domain: string;
  topic: string;
  objectives: string[];
  maximum_examples: number;
  status: string;
  metrics: Record<string, unknown>;
};

export type ReviewItem = {
  review_id: string;
  candidate_id: string;
  question_id: string;
  status: string;
  reviewer_id: string | null;
  reviewer_note: string | null;
};

export type DatasetCandidate = {
  dataset_candidate_id: string;
  dataset_type: string;
  status: string;
  record_ids: string[];
};

export type DatasetVersion = {
  dataset_version_id: string;
  name: string;
  dataset_type: string;
  approved_record_count: number;
  approval_status: string;
  content_manifest_hash: string;
};

export type ModelCandidate = {
  candidate_id: string;
  base_model: string;
  dataset_version: string;
  approval_state: string;
  deployment_recommendation: string;
};

export type StudentAnswer = {
  answer: string;
  confidence: number;
  topic: string | null;
  evidence_status: string;
  limitations: string[];
  sources: Array<{
    source_id: string;
    document_id: string;
    title: string;
    url: string | null;
    section: string | null;
    page: number | null;
    relevance_score: number;
  }>;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: { accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const [health, readiness] = await Promise.all([
    getJson<HealthResponse>("/api/v1/health"),
    getJson<ReadinessResponse>("/api/v1/ready"),
  ]);
  return { health, readiness };
}

export async function fetchSources(): Promise<Source[]> {
  const result = await getJson<{ sources: Source[] }>("/api/v1/technology/sources");
  return result.sources;
}

export async function fetchCurriculum(): Promise<CurriculumTopic[]> {
  const result = await getJson<{ topics: CurriculumTopic[] }>("/api/v1/technology/student/curriculum");
  return result.topics;
}

export async function fetchLearningCurriculum(): Promise<CoverageReport> {
  return getJson<CoverageReport>("/api/v1/technology/learning/curriculum");
}

export async function fetchKnowledgeGaps(): Promise<KnowledgeGap[]> {
  const result = await getJson<{ gaps: KnowledgeGap[] }>("/api/v1/technology/learning/curriculum/gaps");
  return result.gaps;
}

export async function fetchLearningCycles(): Promise<LearningCycle[]> {
  const result = await getJson<{ cycles: LearningCycle[] }>("/api/v1/technology/learning/cycles");
  return result.cycles;
}

export async function fetchPendingReviews(): Promise<ReviewItem[]> {
  const result = await getJson<{ reviews: ReviewItem[] }>("/api/v1/technology/learning/reviews");
  return result.reviews;
}

export async function approveReview(reviewId: string): Promise<ReviewItem> {
  const response = await fetch(`${apiBaseUrl}/api/v1/technology/learning/reviews/${reviewId}/approve`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      accept: "application/json",
      "x-devmind-admin": "local-admin",
    },
    body: JSON.stringify({ reviewer_id: "local-admin", note: "Approved in local admin mode." }),
  });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<ReviewItem>;
}

export async function fetchDatasetRegistry(): Promise<{
  dataset_candidates: DatasetCandidate[];
  dataset_versions: DatasetVersion[];
}> {
  const [candidates, versions] = await Promise.all([
    getJson<{ dataset_candidates: DatasetCandidate[] }>("/api/v1/technology/learning/dataset-candidates"),
    getJson<{ dataset_versions: DatasetVersion[] }>("/api/v1/technology/learning/dataset-versions"),
  ]);
  return { dataset_candidates: candidates.dataset_candidates, dataset_versions: versions.dataset_versions };
}

export async function fetchModelCandidates(): Promise<ModelCandidate[]> {
  const result = await getJson<{ model_candidates: ModelCandidate[] }>("/api/v1/technology/learning/model-candidates");
  return result.model_candidates;
}

export async function askTechnologyStudent(question: string): Promise<StudentAnswer> {
  const response = await fetch(`${apiBaseUrl}/api/v1/technology/student/ask`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<StudentAnswer>;
}
