import type { RepoInfo } from "@/lib/api";

export function RepoInfoCard({ info }: { info: RepoInfo }) {
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-accent)] animate-pulse" />
        <span className="font-mono text-[10px] tracking-widest text-[var(--color-muted)] uppercase">
          Target lock // metadata
        </span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div>
          <p className="font-mono text-[10px] text-[var(--color-muted)] uppercase mb-1">Language</p>
          <p className="font-mono text-sm">{info.language ?? "Unknown"}</p>
        </div>
        <div>
          <p className="font-mono text-[10px] text-[var(--color-muted)] uppercase mb-1">Stars</p>
          <p className="font-mono text-sm text-[var(--color-accent)]">
            ★ {info.stars.toLocaleString()}
          </p>
        </div>
        <div>
          <p className="font-mono text-[10px] text-[var(--color-muted)] uppercase mb-1">Size</p>
          <p className="font-mono text-sm">{info.size_kb.toLocaleString()} KB</p>
        </div>
        <div>
          <p className="font-mono text-[10px] text-[var(--color-muted)] uppercase mb-1">Branch</p>
          <p className="font-mono text-sm">{info.default_branch}</p>
        </div>
      </div>
      {info.description && (
        <p className="mt-3 pt-3 border-t border-dashed border-[var(--color-border)] font-mono text-xs text-[var(--color-muted)]">
          {info.description}
        </p>
      )}
    </div>
  );
}