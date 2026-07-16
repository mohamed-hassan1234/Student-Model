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
