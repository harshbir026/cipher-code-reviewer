"use client";

import { useEffect, useState } from "react";

function gradeFor(score: number): { grade: string; color: string } {
  if (score >= 90) return { grade: "A", color: "var(--color-accent)" };
  if (score >= 75) return { grade: "B", color: "var(--color-low)" };
  if (score >= 60) return { grade: "C", color: "var(--color-medium)" };
  if (score >= 40) return { grade: "D", color: "var(--color-high)" };
  return { grade: "F", color: "var(--color-critical)" };
}

export function HealthGauge({
  score,
  totalFindings,
  highPriorityCount,
}: {
  score: number;
  totalFindings: number;
  highPriorityCount: number;
}) {
  const { grade, color } = gradeFor(score);
  const circumference = 251.2;
  const [offset, setOffset] = useState(circumference);

  useEffect(() => {
    const id = requestAnimationFrame(() =>
      setOffset(circumference - (score / 100) * circumference),
    );
    return () => cancelAnimationFrame(id);
  }, [score]);

  return (
    <div className="relative flex items-center justify-between overflow-hidden rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-6 mb-4">
      <span
        className="pointer-events-none absolute right-5 top-1/2 -translate-y-1/2 font-display text-8xl font-extrabold opacity-[0.05] select-none"
        style={{ color }}
      >
        {grade}
      </span>

      <div className="relative flex h-24 w-24 shrink-0 items-center justify-center">
        <svg className="h-24 w-24 -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="40" fill="none" stroke="var(--color-border)" strokeWidth="8" />
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 1.2s cubic-bezier(0.16,1,0.3,1)" }}
          />
        </svg>
        <span className="absolute font-display text-2xl font-extrabold">{score}</span>
      </div>

      <div className="relative z-10 ml-8 flex-1">
        <p className="font-mono text-[10px] uppercase tracking-widest text-[var(--color-muted)]">
          Codebase integrity
        </p>
        <p className="mt-1 max-w-md font-mono text-xs text-[var(--color-muted)]">
          AI evaluation complete. Parsed and analyzed for security, performance, and
          architectural risk.
        </p>
        <div className="mt-3 flex gap-3">
          <span className="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-1.5 font-mono text-xs">
            <b className="text-[var(--color-accent)]">{totalFindings}</b> findings
          </span>
          <span
            className="rounded border px-3 py-1.5 font-mono text-xs"
            style={{
              borderColor: highPriorityCount > 0 ? "var(--color-critical)" : "var(--color-border)",
            }}
          >
            <b style={{ color: highPriorityCount > 0 ? "var(--color-critical)" : "var(--color-accent)" }}>
              {highPriorityCount}
            </b>{" "}
            high priority
          </span>
        </div>
      </div>
    </div>
  );
}