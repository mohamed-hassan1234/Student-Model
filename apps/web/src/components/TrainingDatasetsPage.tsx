import { useEffect, useState } from "react";

import {
  fetchDatasetRegistry,
  fetchTrainingDatasetValidation,
  type DatasetVersion,
  type TrainingDatasetValidationReport,
} from "../api/client";

export function TrainingDatasetsPage() {
  const [versions, setVersions] = useState<DatasetVersion[]>([]);
  const [report, setReport] = useState<TrainingDatasetValidationReport | null>(null);

  useEffect(() => {
    let active = true;
    fetchDatasetRegistry().then(async (result) => {
      if (!active) return;
      setVersions(result.dataset_versions);
      const first = result.dataset_versions[0];
      if (first) setReport(await fetchTrainingDatasetValidation(first.dataset_version_id));
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-semibold text-ink">Training Datasets</h2>
      {versions.length === 0 ? <p>No approved dataset versions are available.</p> : null}
      {versions.map((version) => (
        <article key={version.dataset_version_id} className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="font-semibold text-ink">{version.name}</h3>
          <p className="text-sm text-graphite">Version: {version.dataset_version_id}</p>
          <p className="text-sm text-graphite">Approved records: {version.approved_record_count}</p>
          <p className="text-sm text-graphite">Approval: {version.approval_status}</p>
        </article>
      ))}
      {report ? (
        <article className="rounded-md border border-slate-200 bg-white p-4">
          <h3 className="font-semibold text-ink">Latest Validation</h3>
          <p className="text-sm text-graphite">Valid: {String(report.valid)}</p>
          <p className="text-sm text-graphite">Train/validation/test: {report.training_count}/{report.validation_count}/{report.held_out_test_count}</p>
          <p className="text-sm text-graphite">Secret scan: {report.secret_scan_result}</p>
          <p className="text-sm text-graphite">Blocking issues: {report.blocking_issues.join(", ") || "none"}</p>
        </article>
      ) : null}
    </section>
  );
}
