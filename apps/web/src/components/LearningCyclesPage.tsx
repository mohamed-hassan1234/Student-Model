import { useEffect, useState } from "react";

import { fetchLearningCycles, type LearningCycle } from "../api/client";
import { StatusBadge } from "./StatusBadge";

export function LearningCyclesPage() {
  const [cycles, setCycles] = useState<LearningCycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void fetchLearningCycles()
      .then((result) => {
        if (active) {
          setCycles(result);
        }
      })
      .catch(() => {
        if (active) {
          setError("Learning cycles are unavailable.");
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
        <h2 className="text-2xl font-semibold text-ink">Learning Cycles</h2>
        <p className="mt-1 text-sm text-graphite">Cycles are bounded, resumable, and require human approval before dataset use.</p>
      </header>
      <div className="rounded-md border border-slate-200 bg-white p-4">
        <h3 className="font-semibold text-ink">Create cycle</h3>
        <p className="mt-1 text-sm text-graphite">Use the API with admin placeholder authorization to create a planned cycle. Provider calls remain bounded by configuration.</p>
      </div>
      {loading ? <p aria-label="Loading learning cycles" className="text-sm text-graphite">Loading learning cycles...</p> : null}
      {error ? <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      {!loading && !error && cycles.length === 0 ? <p className="text-sm text-graphite">No learning cycles have been created.</p> : null}
      <div className="space-y-3">
        {cycles.map((cycle) => (
          <article key={cycle.cycle_id} className="rounded-md border border-slate-200 bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold text-ink">{cycle.topic}</h3>
                <p className="text-sm text-graphite">{cycle.domain}</p>
              </div>
              <StatusBadge label={cycle.status} tone={cycle.status === "failed" ? "warning" : "loading"} />
            </div>
            <p className="mt-3 text-sm text-graphite">Maximum examples: {cycle.maximum_examples}</p>
            <p className="text-sm text-graphite">Objectives: {cycle.objectives.join(", ")}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
