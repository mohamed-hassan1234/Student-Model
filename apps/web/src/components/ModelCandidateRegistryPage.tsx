import { useEffect, useState } from "react";

import { fetchModelCandidates, type ModelCandidate } from "../api/client";
import { StatusBadge } from "./StatusBadge";

export function ModelCandidateRegistryPage() {
  const [candidates, setCandidates] = useState<ModelCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void fetchModelCandidates()
      .then((result) => {
        if (active) {
          setCandidates(result);
        }
      })
      .catch(() => {
        if (active) {
          setError("Model candidate registry is unavailable.");
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="space-y-4">
      <header>
        <h2 className="text-2xl font-semibold text-ink">Model Candidate Registry</h2>
        <p className="mt-1 text-sm text-graphite">Candidates are records for future evaluation. They are not production models.</p>
      </header>
      {loading ? <p aria-label="Loading model candidates" className="text-sm text-graphite">Loading model candidates...</p> : null}
      {error ? <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      {!loading && !error && candidates.length === 0 ? <p className="text-sm text-graphite">No model candidates registered.</p> : null}
      <div className="space-y-3">
        {candidates.map((candidate) => (
          <article key={candidate.candidate_id} className="rounded-md border border-slate-200 bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold text-ink">{candidate.base_model}</h3>
                <p className="text-sm text-graphite">Dataset: {candidate.dataset_version}</p>
              </div>
              <StatusBadge label={candidate.approval_state} tone={candidate.approval_state === "approved" ? "healthy" : "warning"} />
            </div>
            <p className="mt-3 text-sm text-graphite">Recommendation: {candidate.deployment_recommendation}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
