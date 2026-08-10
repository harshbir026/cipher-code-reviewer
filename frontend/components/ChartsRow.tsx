"use client";

import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ReviewComment } from "@/lib/api";

export function ChartsRow({ findings }: { findings: ReviewComment[] }) {
  const byFile = Object.entries(
    findings.reduce<Record<string, number>>((acc, f) => {
      const short = f.file_path.split("/").pop() ?? f.file_path;
      acc[short] = (acc[short] ?? 0) + 1;
      return acc;
    }, {}),
  )
    .map(([file, count]) => ({ file, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 8);

  const severityOrder = ["Critical", "High", "Medium", "Low"];
  const severityColor: Record<string, string> = {
    Critical: "#f87171",
    High: "#fb923c",
    Medium: "#fbbf24",
    Low: "#60a5fa",
  };
  const bySeverity = severityOrder.map((s) => ({
    severity: s,
    count: findings.filter((f) => f.severity === s).length,
  }));

  return (
    <div className="grid sm:grid-cols-2 gap-4 mb-4">
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-4">
        <p className="font-mono text-[10px] uppercase tracking-widest text-[var(--color-muted)] mb-3">
          Issues by file
        </p>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={byFile} layout="vertical" margin={{ left: 8 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="file"
              width={100}
              tick={{ fill: "#7c8598", fontSize: 10, fontFamily: "monospace" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: "#131826",
                border: "1px solid #232a3d",
                fontSize: 12,
                fontFamily: "monospace",
              }}
            />
            <Bar dataKey="count" fill="#5eead4" radius={[0, 3, 3, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-4">
        <p className="font-mono text-[10px] uppercase tracking-widest text-[var(--color-muted)] mb-3">
          Severity breakdown
        </p>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={bySeverity}>
            <XAxis
              dataKey="severity"
              tick={{ fill: "#7c8598", fontSize: 10, fontFamily: "monospace" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis hide />
            <Tooltip
              contentStyle={{
                background: "#131826",
                border: "1px solid #232a3d",
                fontSize: 12,
                fontFamily: "monospace",
              }}
            />
            <Bar dataKey="count" radius={[3, 3, 0, 0]}>
              {bySeverity.map((entry) => (
                <Bar key={entry.severity} dataKey="count" fill={severityColor[entry.severity]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}