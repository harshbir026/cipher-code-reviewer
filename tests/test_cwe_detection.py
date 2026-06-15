"""
CWE detection tests for CWE-79 (XSS) and CWE-89 (SQL Injection).

Three test cases:
1. Unit test — classify_cwe() correctly maps XSS keywords to CWE-79
2. Unit test — classify_cwe() correctly maps SQLi keywords to CWE-89
3. Integration test — LLM detects XSS and SQLi in golden dataset (requires API key)
"""

import os
import shutil
import tempfile

import pytest

from pipeline.parser import ASTParser
from pipeline.reviewer import LLMReviewer, classify_cwe
from utils.token_counter import batch_code_blocks

# Path to the golden dataset file
GOLDEN_FILE = os.path.join(
    os.path.dirname(__file__), "golden_dataset", "buggy_sample.py"
)

# The two new functions we are testing detection of
XSS_FUNCTION = "render_user_profile"  # CWE-79
SQLI_FUNCTION = "get_user_by_email"  # CWE-89


# ── Test 1: Unit test — CWE-79 XSS keyword classification ────────────────────


class TestCWE79Classification:
    """
    Verifies classify_cwe() correctly maps XSS-related keywords to CWE-79.
    No LLM call — pure unit test of the keyword matching logic.
    """

    def test_xss_keyword_maps_to_cwe_79(self):
        """Exact keyword 'xss' must return CWE-79."""
        result = classify_cwe("This function is vulnerable to xss attacks.")
        assert result is not None, "Expected CWE classification, got None"
        cwe_id, url = result
        assert cwe_id == "CWE-79", f"Expected CWE-79, got {cwe_id}"
        assert "79" in url, "URL must reference CWE-79"

    def test_cross_site_scripting_phrase_maps_to_cwe_79(self):
        """Full phrase 'cross-site scripting' must also return CWE-79."""
        result = classify_cwe(
            "User input is embedded in HTML without escaping, "
            "enabling cross-site scripting attacks."
        )
        assert result is not None, "Expected CWE classification for XSS phrase"
        cwe_id, _ = result
        assert cwe_id == "CWE-79", f"Expected CWE-79, got {cwe_id}"

    def test_html_injection_phrase_maps_to_cwe_79(self):
        """'html injection' variant must also map to CWE-79."""
        result = classify_cwe(
            "Direct html injection is possible through the username parameter."
        )
        assert result is not None
        cwe_id, _ = result
        assert cwe_id == "CWE-79"

    def test_non_xss_comment_does_not_match_cwe_79(self):
        """A generic comment with no XSS keywords must return None."""
        result = classify_cwe(
            "This function has a performance issue with large inputs."
        )
        # Should either be None or a different CWE — must NOT be CWE-79
        if result is not None:
            cwe_id, _ = result
            assert (
                cwe_id != "CWE-79"
            ), "Non-XSS comment incorrectly classified as CWE-79"


# ── Test 2: Unit test — CWE-89 SQLi keyword classification ───────────────────


class TestCWE89Classification:
    """
    Verifies classify_cwe() correctly maps SQL injection keywords to CWE-89.
    No LLM call — pure unit test of the keyword matching logic.
    """

    def test_sql_injection_phrase_maps_to_cwe_89(self):
        """Exact phrase 'sql injection' must return CWE-89."""
        result = classify_cwe(
            "This function is vulnerable to sql injection via string concatenation."
        )
        assert result is not None, "Expected CWE classification, got None"
        cwe_id, url = result
        assert cwe_id == "CWE-89", f"Expected CWE-89, got {cwe_id}"
        assert "89" in url, "URL must reference CWE-89"

    def test_sqli_abbreviation_maps_to_cwe_89(self):
        """Abbreviation 'sqli' must also return CWE-89."""
        result = classify_cwe("Classic sqli vulnerability detected in query builder.")
        assert result is not None, "Expected CWE classification for sqli abbreviation"
        cwe_id, _ = result
        assert cwe_id == "CWE-89", f"Expected CWE-89, got {cwe_id}"

    def test_parameterized_query_hint_maps_to_cwe_89(self):
        """
        'parameterized quer' substring maps to CWE-89.
        This covers LLM comments like 'use parameterized queries instead.'
        """
        result = classify_cwe(
            "Replace string concatenation with parameterized queries to prevent injection."
        )
        assert result is not None
        cwe_id, _ = result
        assert cwe_id == "CWE-89"

    def test_non_sqli_comment_does_not_match_cwe_89(self):
        """A comment about division by zero must not map to CWE-89."""
        result = classify_cwe(
            "Missing zero division check will raise ZeroDivisionError."
        )
        if result is not None:
            cwe_id, _ = result
            assert (
                cwe_id != "CWE-89"
            ), "Non-SQLi comment incorrectly classified as CWE-89"


# ── Test 3: Integration test — LLM recall on new XSS + SQLi functions ────────


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OPENAI_API_KEY — skipped in CI without key",
)
def test_xss_and_sqli_golden_recall():
    """
    End-to-end integration test.

    Runs the full pipeline (parse → batch → LLM) against buggy_sample.py
    and verifies the agent detects BOTH new vulnerable functions:
      - render_user_profile (CWE-79: XSS)
      - get_user_by_email   (CWE-89: SQL Injection)

    Also checks that classify_cwe() correctly tags each finding
    with the expected CWE ID.

    Asserts: 100% recall on the two new CWE categories.
    """
    # ── Run the pipeline against the golden dataset ──
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copy(GOLDEN_FILE, os.path.join(tmpdir, "buggy_sample.py"))
        blocks = ASTParser.extract_code_blocks(tmpdir)
        batches = batch_code_blocks(blocks)
        reviewer = LLMReviewer()
        all_reviews = reviewer.analyze_all_batches(batches)

    # ── Build a lookup: function_name → list of ReviewComment ──
    findings_by_function: dict[str, list] = {}
    for review in all_reviews:
        findings_by_function.setdefault(review.function_name, []).append(review)

    found_functions = set(findings_by_function.keys())

    # ── Assert XSS function was flagged ──
    assert XSS_FUNCTION in found_functions, (
        f"Agent did NOT flag '{XSS_FUNCTION}' (CWE-79: XSS). "
        f"Functions found: {found_functions}"
    )

    # ── Assert SQLi function was flagged ──
    assert SQLI_FUNCTION in found_functions, (
        f"Agent did NOT flag '{SQLI_FUNCTION}' (CWE-89: SQLi). "
        f"Functions found: {found_functions}"
    )

    # ── Verify CWE classification tags the XSS finding as CWE-79 ──
    xss_reviews = findings_by_function[XSS_FUNCTION]
    xss_cwe_ids = set()
    for review in xss_reviews:
        cwe = classify_cwe(review.comment)
        if cwe:
            xss_cwe_ids.add(cwe[0])

    assert "CWE-79" in xss_cwe_ids, (
        f"XSS finding in '{XSS_FUNCTION}' was not classified as CWE-79. "
        f"CWEs found: {xss_cwe_ids}. "
        f"Comments: {[r.comment for r in xss_reviews]}"
    )

    # ── Verify CWE classification tags the SQLi finding as CWE-89 ──
    sqli_reviews = findings_by_function[SQLI_FUNCTION]
    sqli_cwe_ids = set()
    for review in sqli_reviews:
        cwe = classify_cwe(review.comment)
        if cwe:
            sqli_cwe_ids.add(cwe[0])

    assert "CWE-89" in sqli_cwe_ids, (
        f"SQLi finding in '{SQLI_FUNCTION}' was not classified as CWE-89. "
        f"CWEs found: {sqli_cwe_ids}. "
        f"Comments: {[r.comment for r in sqli_reviews]}"
    )

    # ── Print recall summary ──
    print(f"\n✓ XSS detection: {XSS_FUNCTION} flagged and classified as CWE-79")
    print(f"✓ SQLi detection: {SQLI_FUNCTION} flagged and classified as CWE-89")
    print(f"✓ All {len(all_reviews)} findings across golden dataset")
    print("✓ 100% recall on new CWE-79 and CWE-89 categories")
