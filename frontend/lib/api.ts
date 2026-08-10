const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type IssueCategory =
  | "Security"
  | "Performance"
  | "Bug"
  | "Style"
  | "Maintainability"
  | "Documentation";

export type Severity = "Low" | "Medium" | "High" | "Critical";

export interface ReviewComment {
  file_path: string;
  function_name: string;
  line_number: number;
  issue_category: IssueCategory;
  severity: Severity;
  comment: string;
  suggested_fix: string;
  vulnerable_snippet: string;
  impact: string;
  confidence_score: number;
  needs_verification: boolean;
}

export interface ReviewResponse {
  repo_url: string;
  total_findings: number;
  health_score: number;
  findings: ReviewComment[];
}

export interface RepoInfo {
  language: string | null;
  stars: number;
  size_kb: number;
  default_branch: string;
  description: string;
}

export class ReviewApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = "ReviewApiError";
    this.status = status;
  }
}

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // not JSON — keep statusText
    }
    throw new ReviewApiError(detail, response.status);
  }
  return response.json();
}

export async function reviewRepository(
  repoUrl: string,
  maxBatches = 10,
): Promise<ReviewResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_url: repoUrl, max_batches: maxBatches }),
    });
  } catch {
    throw new ReviewApiError(
      `Couldn't reach the CIPHER API at ${API_BASE_URL}. Is the backend running?`,
    );
  }
  return handle<ReviewResponse>(response);
}

export async function fetchRepoInfo(repoUrl: string): Promise<RepoInfo | null> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/repo-info?repo_url=${encodeURIComponent(repoUrl)}`,
    );
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}