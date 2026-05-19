"""
GitHub API integration for posting inline PR review comments.
Uses the PyGithub library with the modern line+side parameter approach
to bypass legacy diff-position mathematics.
"""

import logging
import os

from dotenv import load_dotenv
from github import Github, GithubException

load_dotenv()
logger = logging.getLogger(__name__)


class GitHubReviewer:
    """
    Posts AI-generated code review comments directly to GitHub Pull Requests.
    """

    def __init__(self, token: str = None):
        token = token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise EnvironmentError(
                "GITHUB_TOKEN not found. "
                "Set it in your .env file to enable PR commenting."
            )
        self.gh = Github(token)

    def get_pr_info(self, repo_name: str, pr_number: int) -> dict:
        """
        Fetches PR metadata needed for posting comments.
        Returns dict with commit_id and list of modified file paths.
        """
        try:
            repo = self.gh.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            files = [f.filename for f in pr.get_files()]
            return {
                "commit_id": pr.head.sha,
                "files": files,
                "title": pr.title,
            }
        except GithubException as e:
            raise RuntimeError(f"Failed to fetch PR info: {e}") from e

    def post_inline_comment(
        self,
        repo_name: str,
        pr_number: int,
        commit_id: str,
        file_path: str,
        comment_body: str,
        line_number: int,
    ) -> bool:
        """
        Posts a single inline review comment to a GitHub Pull Request.

        Uses `line` + `side='RIGHT'` (modern API) instead of the legacy
        `position` parameter which required complex diff-hunk mathematics.
        `side='RIGHT'` refers to the new/incoming version of the file.

        Returns True on success, False on failure (non-crashing).
        """
        try:
            repo = self.gh.get_repo(repo_name)
            pr = repo.get_pull(pr_number)

            pr.create_review_comment(
                body=comment_body,
                commit_id=commit_id,
                path=file_path,
                line=line_number,
                side="RIGHT",
            )
            logger.info(
                f"Posted comment to {repo_name} PR#{pr_number} "
                f"at {file_path}:{line_number}"
            )
            return True

        except GithubException as e:
            logger.error(f"Failed to post comment to {file_path}:{line_number}: {e}")
            return False

    def post_batch_comments(
        self,
        repo_name: str,
        pr_number: int,
        reviews: list[dict],
        max_comments: int = 10,
    ) -> dict:
        """
        Posts multiple review comments from the analysis results.
        Limits to max_comments to avoid spamming the PR.

        Returns a summary dict with success/failure counts.
        """
        pr_info = self.get_pr_info(repo_name, pr_number)
        commit_id = pr_info["commit_id"]
        pr_files = set(pr_info["files"])

        posted = 0
        skipped = 0
        failed = 0

        # Sort by severity — post most critical issues first
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        sorted_reviews = sorted(
            reviews,
            key=lambda r: severity_order.get(r.get("severity", "Low"), 3),
        )

        for review in sorted_reviews[:max_comments]:
            file_path = review.get("file_path", "")

            # Only comment on files that are part of the PR diff
            if file_path not in pr_files:
                logger.info(f"Skipping {file_path} — not in PR diff.")
                skipped += 1
                continue

            body = (
                f"**[AI Code Review] {review['issue_category']} — "
                f"{review['severity']} Severity**\n\n"
                f"{review['comment']}\n\n"
                f"**Suggested fix:** {review['suggested_fix']}\n\n"
                f"*Confidence: {review['confidence_score']}%"
                f"{' — ⚠️ Verify before acting' if review.get('needs_verification') else ''}*"
            )

            success = self.post_inline_comment(
                repo_name=repo_name,
                pr_number=pr_number,
                commit_id=commit_id,
                file_path=file_path,
                comment_body=body,
                line_number=review.get("line_number", 1),
            )

            if success:
                posted += 1
            else:
                failed += 1

        return {"posted": posted, "skipped": skipped, "failed": failed}
