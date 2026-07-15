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
