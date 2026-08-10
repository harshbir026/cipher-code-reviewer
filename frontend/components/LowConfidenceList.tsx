import type { ReviewComment } from "@/lib/api";

const SEVERITY_COLOR: Record<ReviewComment["severity"], string> = {
  Critical: "var(--color-critical)",
  High: "var(--color-high)",
  Medium: "var(--color-medium)",
  Low: "var(--color-low)",
};

export function LowConfidenceList({ findings }: { findings: ReviewComment[] }) {
  if (findings.length === 0) {
    return (
      <p className="font-mono text-xs text-[var(--color-muted)] px-1 py-6">
        // no low-confidence flags
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {findings.map((f, i) => (
        <div
          key={`${f.file_path}-${f.line_number}-${i}`}
          className="rounded-lg border border-[var(--color-border)] border-l-2 bg-[var(--color-surface)] px-3 py-2.5"
          style={{ borderLeftColor: SEVERITY_COLOR[f.severity] }}
        >
          <p className="font-mono text-xs text-[var(--color-muted)] mb-1">
            {f.file_path} → <span className="text-[var(--color-text)]">{f.function_name}</span>
          </p>
          <p className="font-mono text-[10px] text-[var(--color-muted)] mb-1.5">
            {f.severity} · {f.confidence_score}% confidence
          </p>
          <p className="font-mono text-xs text-[var(--color-muted)] leading-relaxed line-clamp-3">
            {f.comment}
          </p>
        </div>
      ))}
    </div>
  );
}