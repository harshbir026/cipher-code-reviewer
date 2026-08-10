export interface ScanHistoryEntry {
  repo: string;
  findings: number;
  critical: number;
  timestamp: string;
}

const KEY = "cipher_scan_history";

export function loadHistory(): ScanHistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "[]");
  } catch {
    return [];
  }
}

export function pushHistory(entry: ScanHistoryEntry): ScanHistoryEntry[] {
  const current = loadHistory();
  const updated = [...current, entry].slice(-10);
  localStorage.setItem(KEY, JSON.stringify(updated));
  return updated;
}