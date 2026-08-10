"use client";

import { useEffect, useState } from "react";
import { ReviewForm } from "@/components/ReviewForm";
import { RepoInfoCard } from "@/components/RepoInfoCard";
import { HealthGauge } from "@/components/HealthGauge";
import { MetricsRow } from "@/components/MetricsRow";
import { FilterBar } from "@/components/FilterBar";
import { ChartsRow } from "@/components/ChartsRow";
import { FindingCard } from "@/components/FindingCard";
import { LowConfidenceList } from "@/components/LowConfidenceList";
import { ScanHistoryPanel } from "@/components/ScanHistoryPanel";
import {
  reviewRepository,
  fetchRepoInfo,
  ReviewApiError,
  type ReviewResponse,
  type RepoInfo,
  type Severity,
  type IssueCategory,
} from "@/lib/api";
import { loadHistory, pushHistory, type ScanHistoryEntry } from "@/lib/history";

type ScanState = "idle" | "running" | "done" | "error";

const ALL_SEVERITIES: Severity[] = ["Critical", "High", "Medium", "Low"];
const ALL_CATEGORIES: IssueCategory[] = [
  "Security",
  "Performance",
  "Bug",
  "Style",
  "Maintainability",
  "Documentation",
];

export default function Home() {
  const [state, setState] = useState<ScanState>("idle");
  const [result, setResult] = useState<ReviewResponse | null>(null);
  const [repoInfo, setRepoInfo] = useState<RepoInfo | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [history, setHistory] = useState<ScanHistoryEntry[]>([]);

  const [severityFilter, setSeverityFilter] = useState<Severity[]>(ALL_SEVERITIES);
  const [categoryFilter, setCategoryFilter] = useState<IssueCategory[]>(ALL_CATEGORIES);
  const [showLowConfidence, setShowLowConfidence] = useState(true);

  useEffect(() => {
    setHistory(loadHistory());
  }, []);

  async function handleSubmit(repoUrl: string) {
    setState("running");
    setErrorMessage("");
    setRepoInfo(null);

    fetchRepoInfo(repoUrl).then(setRepoInfo);

    try {
      const data = await reviewRepository(repoUrl);
      setResult(data);
      setState("done");
      const critical = data.findings.filter((f) => f.severity === "Critical").length;
      setHistory(
        pushHistory({
          repo: repoUrl,
          findings: data.total_findings,
          critical,
          timestamp: new Date().toLocaleTimeString(),
        }),
      );
    } catch (err) {
      const message =
        err instanceof ReviewApiError ? err.message : "Scan failed for an unknown reason.";
      setErrorMessage(message);
      setState("error");
    }
  }

  const filtered =
    result?.findings.filter(
      (f) =>
        severityFilter.includes(f.severity) &&
        categoryFilter.includes(f.issue_category) &&
        (showLowConfidence || !f.needs_verification),
    ) ?? [];

  const highConfidence = filtered.filter((f) => !f.needs_verification);
  const lowConfidence = filtered.filter((f) => f.needs_verification);
  const highPriorityCount =
    result?.findings.filter((f) => f.severity === "Critical" || f.severity === "High").length ?? 0;

  function exportCsv() {
    if (!result) return;
    const headers = [
      "file_path",
      "function_name",
      "line_number",
      "issue_category",
      "severity",
      "comment",
      "suggested_fix",
      "confidence_score",
      "needs_verification",
    ];
    const rows = result.findings.map((f) =>
      headers.map((h) => `"${String(f[h as keyof typeof f]).replace(/"/g, '""')}"`).join(","),
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "cipher_review_report.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="min-h-screen scan-texture">
      <div className="mx-auto max-w-4xl px-6 py-16 sm:py-20">
        <div className="mb-8">
          <p className="font-mono text-xs text-[var(--color-accent)] mb-3 tracking-wide">
            CIPHER · autonomous code review agent
          </p>
          <h1 className="font-display text-3xl sm:text-4xl font-semibold leading-tight mb-3">
            Point it at a repo.
            <br />
            Get a CWE-classified review.
          </h1>
          <p className="text-[var(--color-muted)] max-w-lg">
            CIPHER clones a public repository, parses every function across Python, JavaScript,
            and TypeScript, and flags security issues with confidence-rated, verifiable findings.
          </p>
        </div>

        <ScanHistoryPanel history={history} />

        <ReviewForm onSubmit={handleSubmit} isRunning={state === "running"} />

        <div className="mt-6">
          {state === "running" && (
            <div className="flex items-center gap-2 font-mono text-sm text-[var(--color-muted)] mb-4">
              <span className="inline-block h-2 w-2 rounded-full bg-[var(--color-accent)] animate-pulse" />
              cloning repository, parsing source, running review batches…
            </div>
          )}

          {repoInfo && <RepoInfoCard info={repoInfo} />}

          {state === "error" && (
            <div className="rounded-lg border border-[var(--color-critical)]/40 bg-[var(--color-critical)]/10 px-4 py-3">
              <p className="font-mono text-sm text-[var(--color-critical)]">{errorMessage}</p>
            </div>
          )}

          {state === "done" && result && (
            <>
              {result.findings.length === 0 ? (
                <div className="text-center py-16">
                  <p className="text-3xl text-[var(--color-accent)] mb-2">✓</p>
                  <p className="font-display text-xl font-semibold">Clean codebase.</p>
                  <p className="font-mono text-xs text-[var(--color-muted)] mt-2">
                    No actionable issues identified. Zero findings.
                  </p>
                </div>
              ) : (
                <>
                  <MetricsRow findings={result.findings} />
                  <HealthGauge
                    score={result.health_score}
                    totalFindings={result.total_findings}
                    highPriorityCount={highPriorityCount}
                  />
                  <ChartsRow findings={result.findings} />
                  <FilterBar
                    severityFilter={severityFilter}
                    categoryFilter={categoryFilter}
                    showLowConfidence={showLowConfidence}
                    onSeverityChange={setSeverityFilter}
                    onCategoryChange={setCategoryFilter}
                    onShowLowConfidenceChange={setShowLowConfidence}
                  />

                  <div className="grid lg:grid-cols-[3fr_2fr] gap-6">
                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-widest text-[var(--color-muted)] mb-3">
                        High confidence findings · {highConfidence.length}
                      </p>
                      <div className="space-y-2">
                        {highConfidence.map((f, i) => (
                          <FindingCard key={`${f.file_path}-${f.line_number}-${i}`} finding={f} />
                        ))}
                      </div>
                    </div>

                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-widest text-[var(--color-muted)] mb-3">
                        Needs verification · {lowConfidence.length}
                      </p>
                      <LowConfidenceList findings={lowConfidence} />

                      <button
                        type="button"
                        onClick={exportCsv}
                        className="mt-4 w-full rounded-md border border-[var(--color-accent)] px-3 py-2 font-mono text-xs text-[var(--color-accent)] hover:bg-[var(--color-accent-dim)] transition-colors"
                      >
                        ⬇ Download full report (.csv)
                      </button>
                    </div>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </main>
  );
}