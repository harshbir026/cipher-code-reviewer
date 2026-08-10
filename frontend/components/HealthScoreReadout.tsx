interface HealthScoreReadoutProps {
  score: number;
  totalFindings: number;
  repoUrl: string;
}

function gradeFor(score: number): { grade: string; color: string } {
  if (score >= 90) return { grade: "A", color: "var(--color-accent)" };
  if (score >= 75) return { grade: "B", color: "var(--color-low)" };
  if (score >= 60) return { grade: "C", color: "var(--color-medium)" };
  if (score >= 40) return { grade: "D", color: "var(--color-high)" };
  return { grade: "F", color: "var(--color-critical)" };
}

export function HealthScoreReadout({ score, totalFindings, repoUrl }: HealthScoreReadoutProps) {
  const { grade, color } = gradeFor(score);
  const shortRepo = repoUrl.replace("https://github.com/", "");

  return (
    <div className="flex items-center justify-between rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-5">
      <div>
        <p className="font-mono text-xs text-[var(--color-muted)] mb-1">{shortRepo}</p>
        <p className="font-display text-lg font-medium">
          {totalFindings} {totalFindings === 1 ? "finding" : "findings"}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <div className="text-right">
          <p className="text-xs text-[var(--color-muted)] font-mono">health score</p>
          <p className="font-mono text-xl font-medium" style={{ color }}>
            {score}
            <span className="text-[var(--color-muted)]">/100</span>
          </p>
        </div>
        <div
          className="flex h-11 w-11 items-center justify-center rounded-md border font-display text-xl font-bold"
          style={{ borderColor: color, color }}
        >
          {grade}
        </div>
      </div>
    </div>
  );
}