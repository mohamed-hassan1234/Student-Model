import { useEffect, useState } from "react";

import { fetchKnowledgeGaps, fetchLearningCurriculum, type CoverageReport, type KnowledgeGap } from "../api/client";
import { StatusBadge } from "./StatusBadge";

export function CurriculumDashboardPage() {
  const [coverage, setCoverage] = useState<CoverageReport | null>(null);
  const [gaps, setGaps] = useState<KnowledgeGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [coverageResult, gapResult] = await Promise.all([fetchLearningCurriculum(), fetchKnowledgeGaps()]);
        if (active) {
          setCoverage(coverageResult);
          setGaps(gapResult);
          setError(null);
        }
      } catch {
        if (active) {
          setError("Phase 2 curriculum data is unavailable.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return <p aria-label="Loading curriculum dashboard" className="text-sm text-graphite">Loading curriculum dashboard...</p>;
  }

  if (error) {
    return <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>;
  }

  return (
    <section className="space-y-5">
      <header>
        <p className="text-sm font-semibold uppercase tracking-wide text-signal">Verified learning</p>
        <h2 className="mt-1 text-2xl font-semibold text-ink">Curriculum Dashboard</h2>
        <p className="mt-1 text-sm text-graphite">Coverage reflects approved evidence and review progress, not model training.</p>
      </header>
      <div className="grid gap-3 sm:grid-cols-3">
        <Metric label="Overall coverage" value={`${Math.round((coverage?.overall_coverage_score ?? 0) * 100)}%`} />
        <Metric label="Topics tracked" value={`${coverage?.topic_scores.length ?? 0}`} />
        <Metric label="Open gaps" value={`${gaps.length}`} />
      </div>
      <div className="grid gap-3 lg:grid-cols-2">
        {coverage?.topic_scores.slice(0, 8).map((topic) => (
          <article key={topic.topic_id} className="rounded-md border border-slate-200 bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold text-ink">{topic.topic}</h3>
                <p className="text-sm text-graphite">{topic.domain} / {topic.subtopic}</p>
              </div>
              <StatusBadge label={`${Math.round(topic.current_coverage_score * 100)}%`} tone={topic.current_coverage_score >= 0.6 ? "healthy" : "warning"} />
            </div>
            <dl className="mt-3 grid grid-cols-2 gap-2 text-sm text-graphite">
              <div>Sources: {topic.approved_source_count}</div>
              <div>Documents: {topic.ingested_document_count}</div>
              <div>Verified Qs: {topic.verified_question_count}</div>
              <div>Eval examples: {topic.evaluation_example_count}</div>
            </dl>
            <p className="mt-3 text-sm font-medium text-amber-700">{topic.next_recommended_learning_action}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-graphite">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}
