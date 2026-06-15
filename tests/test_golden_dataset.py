"""
Golden dataset evaluation test.
Verifies the agent finds known bugs in a controlled sample.
"""

import os
import shutil
import tempfile

import pytest

from pipeline.parser import ASTParser
from pipeline.reviewer import LLMReviewer
from utils.token_counter import batch_code_blocks

GOLDEN_FILE = os.path.join(
    os.path.dirname(__file__), "golden_dataset", "buggy_sample.py"
)

EXPECTED_ISSUES = {
    "unsafe_deserialize": "Security",  # CWE-502
    "run_command": "Security",  # CWE-78
    "divide_numbers": "Bug",  # Division by zero
    "fetch_all_users": "Security",  # CWE-89 (original)
    "get_user_by_email": "Security",  # CWE-89 (new)
    "render_user_profile": "Security",  # CWE-79 (new)
}


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OPENAI_API_KEY — skipped in CI without key",
)
def test_golden_dataset_recall():
    """
    Verifies the LLM finds known bugs in the golden dataset.
    Measures recall: did we catch the real issues?
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copy(GOLDEN_FILE, os.path.join(tmpdir, "buggy_sample.py"))
        blocks = ASTParser.extract_code_blocks(tmpdir)
        batches = batch_code_blocks(blocks)
        reviewer = LLMReviewer()
        all_reviews = reviewer.analyze_all_batches(batches)

    found_functions = {r.function_name for r in all_reviews}
    missed = set(EXPECTED_ISSUES.keys()) - found_functions

    recall = len(found_functions & set(EXPECTED_ISSUES.keys())) / len(EXPECTED_ISSUES)
    print(f"\nRecall: {recall:.0%}")
    print(f"Found: {found_functions}")
    print(f"Missed: {missed}")

    # Agent should catch at least 75% of known issues
    assert (
        recall >= 0.75
    ), f"Agent missed too many known bugs. Recall: {recall:.0%}. Missed: {missed}"
