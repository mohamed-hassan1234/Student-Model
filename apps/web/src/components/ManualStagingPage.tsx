import { useEffect, useState } from "react";

import { fetchStagingRequests, type StagingRequest } from "../api/client";

export function ManualStagingPage() {
  const [requests, setRequests] = useState<StagingRequest[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetchStagingRequests()
      .then((items) => {
        if (active) {
          setRequests(items);
          setError(null);
        }
      })
      .catch(() => {
        if (active) {
          setError("Sign in with staging permission to view manual staging requests.");
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
    <section className="rounded-md border border-slate-200 bg-white p-5">
      <h2 className="text-xl font-semibold text-ink">Manual Staging</h2>
      <p className="mt-2 text-sm text-graphite">
        Staging requests record approved manual actions only. Production model configuration is not changed automatically.
      </p>
      {loading ? <p className="mt-3 text-sm text-graphite">Loading staging requests.</p> : null}
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      {!loading && !error && requests.length === 0 ? (
        <p className="mt-3 text-sm text-graphite">No manual staging requests are recorded.</p>
      ) : null}
      <div className="mt-4 grid gap-3">
        {requests.map((request) => (
          <article key={request.staging_request_id} className="rounded-md border border-slate-200 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="font-semibold text-ink">{request.candidate_id}</h3>
              <span className="rounded bg-slate-100 px-2 py-1 text-xs text-graphite">{request.status}</span>
            </div>
            <p className="mt-2 break-all text-xs text-graphite">Adapter hash: {request.adapter_hash}</p>
            <p className="mt-1 text-xs text-graphite">Environment: {request.staging_environment}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
