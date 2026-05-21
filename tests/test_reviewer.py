"""
Unit tests for the LLM reviewer module.
All OpenAI API calls are mocked.
"""

from unittest.mock import patch

import pytest

from pipeline.reviewer import LLMReviewer, ReviewComment


def make_review_comment(**overrides):
    """Helper to create a ReviewComment with all required fields."""
    defaults = {
        "file_path": "test.py",
        "function_name": "foo",
        "line_number": 1,
        "issue_category": "Bug",
        "severity": "High",
        "comment": "Test comment",
        "suggested_fix": "Fix it",
        "vulnerable_snippet": "return x / y",
        "impact": "This could cause a crash.",
        "confidence_score": 90,
        "needs_verification": False,
    }
    defaults.update(overrides)
    return ReviewComment(**defaults)


class TestReviewCommentValidation:
    """Tests for the Pydantic model validators."""

    def test_confidence_score_clamped_above_100(self):
        comment = make_review_comment(confidence_score=150)
        assert comment.confidence_score == 100

    def test_confidence_score_clamped_below_0(self):
        comment = make_review_comment(
            severity="Low",
            confidence_score=-5,
            needs_verification=True,
        )
        assert comment.confidence_score == 0

    def test_needs_verification_synced_with_score(self):
        comment = make_review_comment(
            issue_category="Security",
            severity="Critical",
            comment="SQL injection",
            suggested_fix="Use parameterized queries",
            vulnerable_snippet="query = f'SELECT * FROM users WHERE id = {uid}'",
            impact="Attacker can dump the entire database.",
            confidence_score=90,
            needs_verification=True,  # Inconsistent
        )
        assert comment.needs_verification is False

    def test_low_score_forces_needs_verification(self):
        comment = make_review_comment(
            issue_category="Performance",
            severity="Medium",
            comment="Maybe slow",
            suggested_fix="Consider caching",
            vulnerable_snippet="result = compute(x)",
            impact="Could slow response times under load.",
            confidence_score=60,
            needs_verification=False,  # Inconsistent
        )
        assert comment.needs_verification is True


class TestLLMReviewer:
    """Tests for the reviewer with mocked API."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"})
    def test_reviewer_initializes_with_key(self):
        reviewer = LLMReviewer()
        assert reviewer is not None

    @patch.dict("os.environ", {}, clear=True)
    def test_reviewer_raises_without_key(self):
        with pytest.raises(EnvironmentError, match="OPENAI_API_KEY"):
            LLMReviewer()
