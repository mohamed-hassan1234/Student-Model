import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { fetchDatasetRegistry, type DatasetCandidate, type DatasetVersion } from "../api/client";
import { StatusBadge } from "./StatusBadge";

export function DatasetRegistryPage() {
  const [candidates, setCandidates] = useState<DatasetCandidate[]>([]);
  const [versions, setVersions] = useState<DatasetVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void fetchDatasetRegistry()
      .then((result) => {
        if (active) {
          setCandidates(result.dataset_candidates);
          setVersions(result.dataset_versions);
        }
      })
      .catch(() => {
        if (active) {
          setError("Dataset registry is unavailable.");
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
    <section className="space-y-5">
      <header>
        <h2 className="text-2xl font-semibold text-ink">Dataset Registry</h2>
        <p className="mt-1 text-sm text-graphite">Approved versions are immutable and exported only on explicit request.</p>
      </header>
      {loading ? <p aria-label="Loading dataset registry" className="text-sm text-graphite">Loading dataset registry...</p> : null}
      {error ? <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      <div className="grid gap-4 lg:grid-cols-2">
        <RegistryColumn title="Candidates">
          {candidates.length === 0 ? <p className="text-sm text-graphite">No dataset candidates.</p> : null}
          {candidates.map((candidate) => (
            <article key={candidate.dataset_candidate_id} className="rounded-md border border-slate-200 p-3">
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-semibold text-ink">{candidate.dataset_type}</h3>
                <StatusBadge label={candidate.status} tone="loading" />
              </div>
              <p className="mt-2 text-sm text-graphite">Records: {candidate.record_ids.length}</p>
            </article>
          ))}
        </RegistryColumn>
        <RegistryColumn title="Approved versions">
          {versions.length === 0 ? <p className="text-sm text-graphite">No approved versions.</p> : null}
          {versions.map((version) => (
            <article key={version.dataset_version_id} className="rounded-md border border-slate-200 p-3">
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-semibold text-ink">{version.name}</h3>
                <StatusBadge label={version.approval_status} tone="healthy" />
              </div>
              <p className="mt-2 text-sm text-graphite">Records: {version.approved_record_count}</p>
              <p className="break-all text-xs text-graphite">Manifest: {version.content_manifest_hash}</p>
            </article>
          ))}
        </RegistryColumn>
      </div>
    </section>
  );
}

function RegistryColumn({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <h3 className="mb-3 font-semibold text-ink">{title}</h3>
      <div className="space-y-3">{children}</div>
    </div>
  );
}
