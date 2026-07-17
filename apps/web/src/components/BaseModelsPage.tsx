import { useEffect, useState } from "react";

import { fetchBaseModelManifests, type BaseModelManifest } from "../api/client";

export function BaseModelsPage() {
  const [manifests, setManifests] = useState<BaseModelManifest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetchBaseModelManifests()
      .then((result) => {
        if (active) setManifests(result);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-semibold text-ink">Base Models</h2>
      {loading ? <p>Loading base-model manifests...</p> : null}
      {!loading && manifests.length === 0 ? <p>No base-model manifests are registered.</p> : null}
      <div className="space-y-3">
        {manifests.map((manifest) => (
          <article key={manifest.manifest_id} className="rounded-md border border-slate-200 bg-white p-4">
            <h3 className="font-semibold text-ink">{manifest.model_identifier}</h3>
            <p className="text-sm text-graphite">Revision: {manifest.exact_revision}</p>
            <p className="text-sm text-graphite">License: {manifest.license_name}</p>
            <p className="text-sm text-graphite">Fine-tuning: {manifest.fine_tuning_permission}</p>
            <p className="text-sm text-graphite">Approval: {manifest.approval_status}</p>
            <p className="text-sm text-graphite">Remote code: {manifest.required_trust_remote_code ? "required" : "not required"}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
