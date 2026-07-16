import type { CurriculumTopic } from "../api/client";

export function CurriculumPage({ topics }: { topics: CurriculumTopic[] }) {
  return (
    <section className="space-y-4">
      <header>
        <h2 className="text-2xl font-semibold text-ink">Curriculum</h2>
        <p className="mt-1 text-sm text-graphite">Phase 1 is limited to core web and software engineering topics.</p>
      </header>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {topics.map((topic) => (
          <article key={topic.topic} className="rounded-md border border-slate-200 bg-white p-4">
            <h3 className="font-semibold text-ink">{topic.topic}</h3>
            <p className="mt-2 text-sm text-graphite">Sources: {topic.available_source_count}</p>
            <p className="text-sm text-graphite">Documents: {topic.ingested_document_count}</p>
            <p className="text-sm text-amber-700">Coverage: {topic.coverage}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
