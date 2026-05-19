"""
Unit tests for the LLM reviewer module.
All OpenAI API calls are mocked.
"""

from unittest.mock import patch

import pytest

from pipeline.reviewer import LLMReviewer, ReviewComment


class TestReviewCommentValidation:
    """Tests for the Pydantic model validators."""

    def test_confidence_score_clamped_above_100(self):
        """LLM sometimes returns 105 or similar — must be clamped."""
        comment = ReviewComment(
            file_path="test.py",
            function_name="foo",
            line_number=1,
            issue_category="Bug",
            severity="High",
            comment="Test comment",
            suggested_fix="Fix it",
            confidence_score=150,  # LLM hallucination
            needs_verification=False,
        )
        assert comment.confidence_score == 100

    def test_confidence_score_clamped_below_0(self):
        comment = ReviewComment(
            file_path="test.py",
            function_name="foo",
            line_number=1,
            issue_category="Bug",
            severity="Low",
            comment="Test",
            suggested_fix="Fix",
            confidence_score=-5,
            needs_verification=True,
        )
        assert comment.confidence_score == 0

    def test_needs_verification_synced_with_score(self):
        """If LLM sets score=90 but needs_verification=True, validator fixes it."""
        comment = ReviewComment(
            file_path="test.py",
            function_name="foo",
            line_number=1,
            issue_category="Security",
            severity="Critical",
            comment="SQL injection",
            suggested_fix="Use parameterized queries",
            confidence_score=90,
            needs_verification=True,  # Inconsistent — score says high confidence
        )
        assert comment.needs_verification is False  # Validator corrected it

    def test_low_score_forces_needs_verification(self):
        comment = ReviewComment(
            file_path="test.py",
            function_name="foo",
            line_number=1,
            issue_category="Performance",
            severity="Medium",
            comment="Maybe slow",
            suggested_fix="Consider caching",
            confidence_score=60,
            needs_verification=False,  # LLM was inconsistent
        )
        assert comment.needs_verification is True  # Validator corrected it


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
