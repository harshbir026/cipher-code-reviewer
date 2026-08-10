"use client";

import { useState } from "react";
import type { ReviewComment } from "@/lib/api";
import { classifyCwe } from "@/lib/cwe";

const SEVERITY_COLOR: Record<ReviewComment["severity"], string> = {
  Critical: "var(--color-critical)",
  High: "var(--color-high)",
  Medium: "var(--color-medium)",
  Low: "var(--color-low)",
};

type Feedback = "confirmed" | "false_positive" | null;

export function FindingCard({ finding }: { finding: ReviewComment }) {
  const [open, setOpen] = useState(false);
  const [feedback, setFeedback] = useState<Feedback>(null);
  const color = SEVERITY_COLOR[finding.severity];
  const cwe = classifyCwe(finding.comment);

  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-left"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <span
            className="shrink-0 rounded px-2 py-0.5 text-xs font-mono font-medium"
            style={{ backgroundColor: `${color}22`, color }}
          >
            {finding.severity}
          </span>
          <span className="shrink-0 text-xs font-mono text-[var(--color-muted)]">
            {finding.issue_category}
          </span>
          <span className="truncate font-mono text-xs text-[var(--color-muted)]">
            {finding.file_path} → {finding.function_name}
          </span>
          {cwe && (
            <a
              href={cwe[1]}
              target="_blank"
              rel="noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="shrink-0 rounded border border-[var(--color-low)]/40 px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-low)]"
            >
              {"\u2691"} {cwe[0]}
            </a>
          )}
        </div>
        <span className="shrink-0 font-mono text-xs text-[var(--color-muted)]">
          {open ? "\u2212" : "+"}
        </span>
      </button>

      {open && (
        <div className="px-4 pb-4 pt-1 space-y-3 border-t border-[var(--color-border)]">
          <p className="text-sm pt-3">
            <span className="font-mono text-xs text-[var(--color-muted)]">
              line {finding.line_number} {"\u00b7"} confidence {finding.confidence_score}%
            </span>
          </p>

          {finding.impact && (
            <div className="rounded-md bg-[var(--color-accent-dim)] px-3 py-2 border-l-2 border-[var(--color-accent)]">
              <p className="text-xs text-[var(--color-accent)]">{"\u26a0"} {finding.impact}</p>
            </div>
          )}

          <p className="text-sm text-[var(--color-text)]">{finding.comment}</p>

          {finding.suggested_fix && (
            <div className="grid sm:grid-cols-2 gap-2">
              <div>
                <p className="font-mono text-[10px] text-[var(--color-critical)] mb-1">{"\u2212"} CURRENT</p>
                <pre className="rounded-md bg-[var(--color-bg)] border border-[var(--color-border)] px-3 py-2 font-mono text-xs text-[var(--color-critical)]/90 overflow-x-auto whitespace-pre-wrap">
                  {finding.vulnerable_snippet}
                </pre>
              </div>
              <div>
                <p className="font-mono text-[10px] text-[var(--color-accent)] mb-1">+ SUGGESTED FIX</p>
                <pre className="rounded-md bg-[var(--color-bg)] border border-[var(--color-border)] px-3 py-2 font-mono text-xs text-[var(--color-accent)]/90 overflow-x-auto whitespace-pre-wrap">
                  {finding.suggested_fix}
                </pre>
              </div>
            </div>
          )}

          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={() => setFeedback("confirmed")}
              className={`flex-1 rounded-md px-3 py-1.5 font-mono text-xs border transition-colors ${
                feedback === "confirmed"
                  ? "bg-[var(--color-accent)] text-[#0b0e14] border-[var(--color-accent)]"
                  : "border-[var(--color-border)] text-[var(--color-muted)] hover:border-[var(--color-accent)]"
              }`}
            >
              {feedback === "confirmed" ? "\u2713 Confirmed" : "Confirm issue"}
            </button>
            <button
              type="button"
              onClick={() => setFeedback("false_positive")}
              className={`flex-1 rounded-md px-3 py-1.5 font-mono text-xs border transition-colors ${
                feedback === "false_positive"
                  ? "bg-[var(--color-critical)]/20 text-[var(--color-critical)] border-[var(--color-critical)]"
                  : "border-[var(--color-border)] text-[var(--color-muted)] hover:border-[var(--color-critical)]"
              }`}
            >
              {feedback === "false_positive" ? "\u2717 False positive" : "Mark false positive"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
