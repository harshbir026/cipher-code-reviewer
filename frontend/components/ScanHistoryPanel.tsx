import type { ScanHistoryEntry } from "@/lib/history";

export function ScanHistoryPanel({ history }: { history: ScanHistoryEntry[] }) {
  if (history.length === 0) return null;

  return (
    <div className="mb-4">
      <p className="font-mono text-[10px] uppercase tracking-widest text-[var(--color-muted)] mb-2">
        Scan history
      </p>
      <div className="flex flex-wrap gap-2">
        {[...history].reverse().map((h, i) => (
          <div
            key={i}
            className="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-1.5 font-mono text-[10px] text-[var(--color-muted)]"
          >
            {h.timestamp} · {h.repo.split("/").pop()} · {h.findings} flags
          </div>
        ))}
      </div>
    </div>
  );
}