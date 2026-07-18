import { useEffect, useState } from "react";

import { fetchApprovalRequests, type ApprovalRequest } from "../api/client";

export function GovernanceDashboardPage() {
  const [requests, setRequests] = useState<ApprovalRequest[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetchApprovalRequests()
      .then((items) => {
        if (active) {
          setRequests(items);
          setError(null);
        }
      })
      .catch(() => {
        if (active) {
          setError("Sign in with candidate-review permission to view governance approvals.");
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
      <h2 className="text-xl font-semibold text-ink">Governance Approvals</h2>
      {loading ? <p className="mt-3 text-sm text-graphite">Loading approvals.</p> : null}
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      {!loading && !error && requests.length === 0 ? (
        <p className="mt-3 text-sm text-graphite">No approval requests are waiting.</p>
      ) : null}
      <div className="mt-4 grid gap-3">
        {requests.map((request) => (
          <article key={request.approval_request_id} className="rounded-md border border-slate-200 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="font-semibold text-ink">{request.candidate_id}</h3>
              <span className="rounded bg-slate-100 px-2 py-1 text-xs text-graphite">{request.status}</span>
            </div>
            <p className="mt-2 text-sm text-graphite">{request.reason}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
