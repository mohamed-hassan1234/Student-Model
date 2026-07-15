import type { SystemStatus } from "../api/client";
import { StatusBadge } from "./StatusBadge";

type SystemStatusPageProps = {
  status: SystemStatus | null;
  loading: boolean;
  error: string | null;
};

export function SystemStatusPage({ status, loading, error }: SystemStatusPageProps) {
  const readinessTone = status?.readiness.status === "ready" ? "healthy" : "warning";

  return (
    <main className="min-h-screen bg-slate-50">
      <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-5 py-8 sm:px-8">
        <header className="mb-8 flex flex-col gap-4 border-b border-slate-200 pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-signal">DevMind AI</p>
            <h1 className="mt-2 text-3xl font-semibold text-ink sm:text-4xl">System status</h1>
          </div>
          <StatusBadge
            label={loading ? "Checking" : status?.readiness.status ?? "Unavailable"}
            tone={loading ? "loading" : status ? readinessTone : "warning"}
          />
        </header>

        {loading ? (
          <section aria-label="Loading status" className="rounded-md border border-slate-200 bg-white p-6">
            <div className="h-4 w-40 animate-pulse rounded bg-slate-200" />
            <div className="mt-4 h-20 animate-pulse rounded bg-slate-100" />
          </section>
        ) : null}

        {!loading && error ? (
          <section role="alert" className="rounded-md border border-amber-200 bg-white p-6">
            <h2 className="text-xl font-semibold text-ink">Status unavailable</h2>
            <p className="mt-2 text-graphite">{error}</p>
          </section>
        ) : null}

        {!loading && !error && status ? (
          <section className="grid gap-4 sm:grid-cols-2">
            <article className="rounded-md border border-slate-200 bg-white p-5">
              <h2 className="text-lg font-semibold text-ink">API</h2>
              <p className="mt-2 text-sm text-graphite">
                {status.health.service} {status.health.version}
              </p>
              <StatusBadge label={status.health.status} tone="healthy" />
            </article>
            <article className="rounded-md border border-slate-200 bg-white p-5">
              <h2 className="text-lg font-semibold text-ink">MongoDB readiness</h2>
              <p className="mt-2 text-sm text-graphite">{status.readiness.checks.mongodb?.detail}</p>
              <StatusBadge
                label={status.readiness.checks.mongodb?.available ? "available" : "unavailable"}
                tone={status.readiness.checks.mongodb?.available ? "healthy" : "warning"}
              />
            </article>
          </section>
        ) : null}

        {!loading && !error && !status ? (
          <section className="rounded-md border border-slate-200 bg-white p-6">
            <h2 className="text-xl font-semibold text-ink">No status yet</h2>
            <p className="mt-2 text-graphite">The API has not returned a system status.</p>
          </section>
        ) : null}
      </section>
    </main>
  );
}
