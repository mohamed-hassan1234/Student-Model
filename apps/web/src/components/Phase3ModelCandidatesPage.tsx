import { useEffect, useState } from "react";

import { fetchPhase3ModelCandidates, type Phase3ModelCandidate } from "../api/client";

export function Phase3ModelCandidatesPage() {
  const [candidates, setCandidates] = useState<Phase3ModelCandidate[]>([]);

  useEffect(() => {
    let active = true;
    fetchPhase3ModelCandidates().then((result) => {
      if (active) setCandidates(result);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-semibold text-ink">Phase 3 Model Candidates</h2>
      <p className="text-sm text-graphite">Candidates shown here are not production models and are never promoted automatically.</p>
      {candidates.length === 0 ? <p>No Phase 3 model candidates are registered.</p> : null}
      {candidates.map((candidate) => (
        <article key={candidate.candidate_id} className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="font-semibold text-ink">{candidate.candidate_name}</h3>
          <p className="text-sm text-graphite">Dataset: {candidate.dataset_version}</p>
          <p className="text-sm text-graphite">Approval: {candidate.approval_state}</p>
          <p className="text-sm text-graphite">Safety: {candidate.safety_status}</p>
          <p className="text-sm text-graphite">License: {candidate.license_status}</p>
          <p className="text-sm text-graphite">Recommendation: {candidate.deployment_recommendation}</p>
        </article>
      ))}
    </section>
  );
}
