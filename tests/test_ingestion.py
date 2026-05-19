"""
Unit tests for the repository ingestion module.
Uses mocking to avoid actual network calls during testing.
"""

from unittest.mock import MagicMock, patch

import pytest

from pipeline.ingestion import RepositoryIngestor


class TestURLValidation:
    """Tests for URL format validation."""

    def test_valid_github_url(self):
        ingestor = RepositoryIngestor("https://github.com/owner/repo")
        ingestor.validate_url()  # Should not raise

    def test_valid_github_url_with_git_suffix(self):
        ingestor = RepositoryIngestor("https://github.com/owner/repo.git")
        ingestor.validate_url()  # Should not raise

    def test_invalid_url_no_repo(self):
        ingestor = RepositoryIngestor("https://github.com/owner")
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            ingestor.validate_url()

    def test_invalid_url_wrong_domain(self):
        ingestor = RepositoryIngestor("https://gitlab.com/owner/repo")
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            ingestor.validate_url()

    def test_invalid_url_empty(self):
        ingestor = RepositoryIngestor("")
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            ingestor.validate_url()

    def test_strips_trailing_slash(self):
        ingestor = RepositoryIngestor("https://github.com/owner/repo/")
        assert ingestor.repo_url == "https://github.com/owner/repo"


class TestCloning:
    """Tests for the cloning logic (mocked)."""

    @patch("pipeline.ingestion.Repo")
    def test_clone_returns_temp_dir(self, mock_repo):
        mock_repo.clone_from.return_value = MagicMock()
        ingestor = RepositoryIngestor("https://github.com/owner/repo")
        result = ingestor.clone_and_get_path()
        assert result is not None
        result.cleanup()

    @patch("pipeline.ingestion.Repo")
    def test_clone_calls_depth_1(self, mock_repo):
        mock_repo.clone_from.return_value = MagicMock()
        ingestor = RepositoryIngestor("https://github.com/owner/repo")
        result = ingestor.clone_and_get_path()
        call_kwargs = mock_repo.clone_from.call_args[1]
        assert call_kwargs.get("depth") == 1
        result.cleanup()
