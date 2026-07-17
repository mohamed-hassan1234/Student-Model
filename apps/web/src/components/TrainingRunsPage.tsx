import { useEffect, useState } from "react";

import { fetchTrainingRuns, type TrainingRun } from "../api/client";

export function TrainingRunsPage() {
  const [runs, setRuns] = useState<TrainingRun[]>([]);

  useEffect(() => {
    let active = true;
    fetchTrainingRuns().then((result) => {
      if (active) setRuns(result);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-semibold text-ink">Training Runs</h2>
      {runs.length === 0 ? <p>No training runs have been created.</p> : null}
      {runs.map((run) => (
        <article key={run.run_id} className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="font-semibold text-ink">{run.experiment_name}</h3>
          <p className="text-sm text-graphite">Status: {run.status}</p>
          <p className="text-sm text-graphite">Base model: {run.base_model_identifier}</p>
          <p className="text-sm text-graphite">Dataset: {run.dataset_version}</p>
          <p className="text-sm text-graphite">Step: {run.current_step}</p>
          <p className="text-sm text-graphite">Adapter hash: {run.adapter_hash ?? "not saved"}</p>
          <p className="text-sm text-graphite">Metrics: {run.metrics_location ?? "not recorded"}</p>
        </article>
      ))}
    </section>
  );
}
