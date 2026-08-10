"use client";

import { useState, type FormEvent } from "react";

interface ReviewFormProps {
  onSubmit: (repoUrl: string) => void;
  isRunning: boolean;
}

export function ReviewForm({ onSubmit, isRunning }: ReviewFormProps) {
  const [repoUrl, setRepoUrl] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = repoUrl.trim();
    if (trimmed) onSubmit(trimmed);
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex items-center gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3.5 focus-within:border-[var(--color-accent)] transition-colors">
        <span className="font-mono text-[var(--color-accent)] select-none">$</span>
        <span className="font-mono text-[var(--color-muted)] select-none hidden sm:inline">
          cipher review
        </span>
        <input
          type="text"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          placeholder="https://github.com/owner/repository"
          disabled={isRunning}
          className="flex-1 min-w-0 bg-transparent font-mono text-[var(--color-text)] placeholder:text-[var(--color-muted)]/60 outline-none disabled:opacity-50"
          autoComplete="off"
          spellCheck={false}
        />
        <button
          type="submit"
          disabled={isRunning || !repoUrl.trim()}
          className="shrink-0 rounded-md bg-[var(--color-accent)] px-4 py-1.5 font-display font-semibold text-sm text-[#0b0e14] transition-opacity hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isRunning ? "Scanning…" : "Run scan"}
        </button>
      </div>
    </form>
  );
}