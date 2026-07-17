import { useEffect, useState } from "react";

import { fetchHardwareReport, type HardwareReport } from "../api/client";

export function HardwareAssessmentPage() {
  const [report, setReport] = useState<HardwareReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchHardwareReport()
      .then((result) => {
        if (active) setReport(result);
      })
      .catch(() => {
        if (active) setError("Hardware assessment is not available.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  if (loading) return <section aria-busy="true">Loading hardware assessment...</section>;
  if (error) return <section role="alert">{error}</section>;
  if (!report) return <section>No hardware assessment has been recorded yet.</section>;

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-semibold text-ink">Hardware Assessment</h2>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Metric label="CPU" value={report.cpu} />
        <Metric label="RAM" value={`${report.system_ram_gb} GB`} />
        <Metric label="GPU" value={report.gpu_available ? report.gpu_name ?? "available" : "not available"} />
        <Metric label="GPU memory" value={report.gpu_memory_gb ? `${report.gpu_memory_gb} GB` : "unavailable"} />
        <Metric label="CUDA" value={report.cuda_available ? "available" : "not available"} />
        <Metric label="Disk" value={`${report.available_disk_gb} GB free`} />
      </div>
      <p className="rounded-md border border-slate-200 bg-white p-3 text-sm text-graphite">
        Recommended mode: <strong>{report.recommended_training_mode}</strong>
      </p>
      <ul className="list-disc pl-5 text-sm text-graphite">
        {report.expected_limitations.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-1 font-medium text-ink">{value}</p>
    </div>
  );
}
