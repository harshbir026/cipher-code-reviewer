"""
Repository ingestion module.
Handles GitHub URL validation and shallow repository cloning
into ephemeral temporary directories.
"""

import logging
import re
import tempfile

from git import Repo
from git.exc import GitCommandError

logger = logging.getLogger(__name__)

# Regex to validate GitHub URLs
# Matches: https://github.com/owner/repo or https://github.com/owner/repo.git
GITHUB_URL_PATTERN = re.compile(
    r"^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(\.git)?$"
)


class RepositoryIngestor:
    """
    Clones a public GitHub repository into an ephemeral
    temporary directory for analysis.
    """

    def __init__(self, repo_url: str):
        self.repo_url = repo_url.strip().rstrip("/")

    def validate_url(self) -> None:
        """
        Validates the GitHub URL format before attempting a clone.
        Raises ValueError with a descriptive message on failure.
        """
        if not GITHUB_URL_PATTERN.match(self.repo_url):
            raise ValueError(
                f"Invalid GitHub URL format: '{self.repo_url}'. "
                "Expected format: https://github.com/owner/repository"
            )

    def clone_and_get_path(self) -> tempfile.TemporaryDirectory:
        """
        Validates the URL and performs a shallow clone (depth=1)
        into a temporary directory.

        Returns the TemporaryDirectory object. The caller is responsible
        for calling .cleanup() when done, or using it as a context manager.

        Raises:
            ValueError: If the URL format is invalid.
            RuntimeError: If the clone fails (repo not found, private, etc.)
        """
        self.validate_url()

        temp_dir = tempfile.TemporaryDirectory()
        try:
            logger.info(f"Starting shallow clone: {self.repo_url}")
            Repo.clone_from(
                self.repo_url,
                temp_dir.name,
                depth=1,  # Only latest snapshot, no history
                no_tags=True,  # Skip tags — saves additional network time
            )
            logger.info(f"Clone completed to: {temp_dir.name}")
            return temp_dir

        except GitCommandError as e:
            temp_dir.cleanup()
            error_message = str(e).lower()
            # Provide human-readable errors instead of raw git output
            if "repository not found" in error_message or "not found" in error_message:
                raise RuntimeError(
                    f"Repository not found or is private: {self.repo_url}"
                )
            elif "could not resolve host" in error_message:
                raise RuntimeError(
                    "Network error: could not reach GitHub. "
                    "Check your internet connection."
                )
            else:
                raise RuntimeError(f"Git clone failed: {str(e)}")

        except Exception as e:
            temp_dir.cleanup()
            raise RuntimeError(f"Unexpected error during clone: {str(e)}")
