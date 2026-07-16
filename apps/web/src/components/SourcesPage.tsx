import type { Source } from "../api/client";

type SourcesPageProps = {
  sources: Source[];
  loading: boolean;
  error: string | null;
};

export function SourcesPage({ sources, loading, error }: SourcesPageProps) {
  return (
    <section className="space-y-4">
      <header>
        <h2 className="text-2xl font-semibold text-ink">Sources</h2>
        <p className="mt-1 text-sm text-graphite">
          Register only approved technical sources. Ingestion requires license and human approval.
        </p>
      </header>
      <div className="rounded-md border border-slate-200 bg-white p-4">
        <h3 className="text-lg font-semibold text-ink">Register approved website</h3>
        <p className="mt-1 text-sm text-graphite">
          API endpoint ready: <code>/api/v1/technology/sources</code>
        </p>
      </div>
      <div className="rounded-md border border-slate-200 bg-white p-4">
        <h3 className="text-lg font-semibold text-ink">Upload supported file</h3>
        <p className="mt-1 text-sm text-graphite">PDF, Markdown, plain text, and HTML are supported.</p>
      </div>
      {loading ? <p className="text-sm text-graphite">Loading sources...</p> : null}
      {error ? <p role="alert" className="text-sm font-medium text-amber-700">{error}</p> : null}
      {!loading && !error && sources.length === 0 ? (
        <p className="rounded-md border border-slate-200 bg-white p-4 text-sm text-graphite">
          No approved sources are registered yet.
        </p>
      ) : null}
      <div className="grid gap-3">
        {sources.map((source) => (
          <article key={source.source_id} className="rounded-md border border-slate-200 bg-white p-4">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h3 className="text-lg font-semibold text-ink">{source.name}</h3>
                <p className="text-sm text-graphite">{source.description}</p>
              </div>
              <span className="rounded-md border border-slate-200 px-3 py-1 text-sm text-graphite">
                {source.source_status}
              </span>
            </div>
            <dl className="mt-3 grid gap-2 text-sm text-graphite sm:grid-cols-3">
              <div><dt className="font-medium text-ink">Topic</dt><dd>{source.technology_topic}</dd></div>
              <div><dt className="font-medium text-ink">License</dt><dd>{source.license_type}</dd></div>
              <div><dt className="font-medium text-ink">Ingestion</dt><dd>{source.ingestion_status}</dd></div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}
