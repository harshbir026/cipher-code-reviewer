"use client";

import type { IssueCategory, Severity } from "@/lib/api";

const SEVERITIES: Severity[] = ["Critical", "High", "Medium", "Low"];
const CATEGORIES: IssueCategory[] = [
  "Security",
  "Performance",
  "Bug",
  "Style",
  "Maintainability",
  "Documentation",
];

interface FilterBarProps {
  severityFilter: Severity[];
  categoryFilter: IssueCategory[];
  showLowConfidence: boolean;
  onSeverityChange: (s: Severity[]) => void;
  onCategoryChange: (c: IssueCategory[]) => void;
  onShowLowConfidenceChange: (v: boolean) => void;
}

function toggle<T>(list: T[], item: T): T[] {
  return list.includes(item) ? list.filter((i) => i !== item) : [...list, item];
}

function Pill<T extends string>({
  label,
  active,
  onClick,
}: {
  label: T;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded px-2.5 py-1 font-mono text-[11px] border transition-colors ${
        active
          ? "border-[var(--color-accent)] text-[var(--color-accent)] bg-[var(--color-accent-dim)]"
          : "border-[var(--color-border)] text-[var(--color-muted)] hover:border-[var(--color-muted)]"
      }`}
    >
      {label}
    </button>
  );
}

export function FilterBar({
  severityFilter,
  categoryFilter,
  showLowConfidence,
  onSeverityChange,
  onCategoryChange,
  onShowLowConfidenceChange,
}: FilterBarProps) {
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 mb-4 space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--color-muted)] mr-1">
          Severity
        </span>
        {SEVERITIES.map((s) => (
          <Pill
            key={s}
            label={s}
            active={severityFilter.includes(s)}
            onClick={() => onSeverityChange(toggle(severityFilter, s))}
          />
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--color-muted)] mr-1">
          Category
        </span>
        {CATEGORIES.map((c) => (
          <Pill
            key={c}
            label={c}
            active={categoryFilter.includes(c)}
            onClick={() => onCategoryChange(toggle(categoryFilter, c))}
          />
        ))}
      </div>
      <label className="flex items-center gap-2 font-mono text-xs text-[var(--color-muted)] cursor-pointer w-fit">
        <input
          type="checkbox"
          checked={showLowConfidence}
          onChange={(e) => onShowLowConfidenceChange(e.target.checked)}
          className="accent-[var(--color-accent)]"
        />
        Show low confidence flags
      </label>
    </div>
  );
}