import type { ReviewComment } from "@/lib/api";

export function MetricsRow({ findings }: { findings: ReviewComment[] }) {
  const critical = findings.filter((f) => f.severity === "Critical").length;
  const high = findings.filter((f) => f.severity === "High").length;
  const verify = findings.filter((f) => f.needs_verification).length;
  const avgConfidence = findings.length
    ? Math.round(findings.reduce((sum, f) => sum + f.confidence_score, 0) / findings.length)
    : 0;

  const metrics = [
    { label: "Total flags", value: findings.length },
    { label: "Critical", value: critical },
    { label: "High", value: high },
    { label: "Verify", value: verify },
    { label: "Avg confidence", value: `${avgConfidence}%` },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-4">
      {metrics.map((m) => (
        <div
          key={m.label}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3"
        >
          <p className="font-mono text-[10px] uppercase tracking-widest text-[var(--color-muted)]">
            {m.label}
          </p>
          <p className="font-mono text-2xl mt-1 text-[var(--color-accent)]">{m.value}</p>
        </div>
      ))}
    </div>
  );
}