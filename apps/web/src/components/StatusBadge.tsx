type StatusBadgeProps = {
  label: string;
  tone: "healthy" | "warning" | "loading";
};

const toneClassName = {
  healthy: "border-emerald-200 bg-emerald-50 text-emerald-800",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  loading: "border-slate-200 bg-slate-50 text-slate-700",
};

export function StatusBadge({ label, tone }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex min-h-8 items-center rounded-md border px-3 text-sm font-medium ${toneClassName[tone]}`}
    >
      {label}
    </span>
  );
}
