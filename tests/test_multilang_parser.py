"""
Multi-language parser tests for tree-sitter based JS/TS extraction.

Three test cases:
1. Unit test — TreeSitterParser correctly extracts JS functions with
   correct name/type/language tagging (guards the earlier
   `function_expression` -> `function` node-type fix)
2. Unit test — TreeSitterParser correctly extracts TS classes/methods
   (guards the `type_identifier` vs `identifier` field regression)
3. Integration test — LLM detects XSS and SQLi in the JS golden dataset,
   using the same CWE classification pipeline as the Python tests
   (requires API key)
"""

import os
import shutil
import tempfile

import pytest

from pipeline.parser import extract_all_code_blocks
from pipeline.reviewer import LLMReviewer, classify_cwe
from pipeline.ts_parser import TreeSitterParser
from utils.token_counter import batch_code_blocks

GOLDEN_JS_FILE = os.path.join(
    os.path.dirname(__file__), "golden_dataset", "xss_sqli_sample.js"
)
GOLDEN_TS_FILE = os.path.join(
    os.path.dirname(__file__), "golden_dataset", "class_sample.ts"
)

XSS_FUNCTION = "renderComment"  # CWE-79
SQLI_FUNCTION = "getUserByEmail"  # CWE-89


# ── Test 1: Unit test — JS function extraction ────────────────────────────


class TestJSFunctionExtraction:
    """
    Verifies TreeSitterParser correctly extracts JS functions with the
    right name, type, and language tag. No LLM call — pure parser test.
    """

    def _extract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy(GOLDEN_JS_FILE, os.path.join(tmpdir, "xss_sqli_sample.js"))
            return TreeSitterParser.extract_code_blocks(tmpdir)

    def test_xss_function_extracted(self):
        """renderComment must be extracted as a JS function block."""
        blocks = self._extract()
        names = {b["name"] for b in blocks}
        assert XSS_FUNCTION in names, f"Expected '{XSS_FUNCTION}' in {names}"

    def test_sqli_function_extracted(self):
        """getUserByEmail must be extracted as a JS function block."""
        blocks = self._extract()
        names = {b["name"] for b in blocks}
        assert SQLI_FUNCTION in names, f"Expected '{SQLI_FUNCTION}' in {names}"

    def test_blocks_tagged_as_javascript(self):
        """Every extracted block from a .js file must carry language='javascript'."""
        blocks = self._extract()
        assert blocks, "Expected at least one extracted block"
        for block in blocks:
            assert block["language"] == "javascript", (
                f"Expected language='javascript', got '{block['language']}' "
                f"for block '{block['name']}'"
            )

    def test_blocks_typed_as_function(self):
        """Both golden functions must be typed 'function', not misclassified."""
        blocks = self._extract()
        types_by_name = {b["name"]: b["type"] for b in blocks}
        assert types_by_name.get(XSS_FUNCTION) == "function"
        assert types_by_name.get(SQLI_FUNCTION) == "function"


# ── Test 2: Unit test — TS class/method extraction ─────────────────────────


class TestTSClassExtraction:
    """
    Verifies TreeSitterParser correctly extracts TS classes and methods.
    Regression guard for the class_declaration `type_identifier` field
    bug (TS grammar names the class-name field differently than JS).
    """

    def _extract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy(GOLDEN_TS_FILE, os.path.join(tmpdir, "class_sample.ts"))
            return TreeSitterParser.extract_code_blocks(tmpdir)

    def test_class_extracted_with_correct_name(self):
        """UserValidator must be extracted as a class block, not skipped."""
        blocks = self._extract()
        class_blocks = [b for b in blocks if b["type"] == "class"]
        names = {b["name"] for b in class_blocks}
        assert "UserValidator" in names, (
            f"Expected class 'UserValidator' in {names} — "
            "class_declaration query may have regressed to using "
            "'identifier' instead of 'type_identifier'."
        )

    def test_method_extracted_with_correct_name(self):
        """validateEmail must be extracted as a method block."""
        blocks = self._extract()
        method_blocks = [b for b in blocks if b["type"] == "method"]
        names = {b["name"] for b in method_blocks}
        assert "validateEmail" in names, f"Expected method 'validateEmail' in {names}"

    def test_blocks_tagged_as_typescript(self):
        """Every extracted block from a .ts file must carry language='typescript'."""
        blocks = self._extract()
        assert blocks, "Expected at least one extracted block"
        for block in blocks:
            assert block["language"] == "typescript"


# ── Test 3: Orchestrator — merges Python + JS/TS blocks ────────────────────


class TestOrchestratorMerge:
    """
    Verifies extract_all_code_blocks() (pipeline.parser) merges
    ASTParser (Python) and TreeSitterParser (JS/TS) output without
    dropping or mislabeling blocks from either.
    """

    def test_merged_extraction_includes_all_languages(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy(GOLDEN_JS_FILE, os.path.join(tmpdir, "xss_sqli_sample.js"))
            shutil.copy(GOLDEN_TS_FILE, os.path.join(tmpdir, "class_sample.ts"))
            blocks = extract_all_code_blocks(tmpdir)

        languages = {b["language"] for b in blocks}
        assert "javascript" in languages
        assert "typescript" in languages


# ── Test 4: Integration test — LLM recall on JS XSS + SQLi ─────────────────


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OPENAI_API_KEY — skipped in CI without key",
)
def test_js_xss_and_sqli_golden_recall():
    """
    End-to-end integration test, mirroring test_cwe_detection.py's
    Python equivalent but against the JS golden dataset.

    Runs the full pipeline (tree-sitter parse -> batch -> LLM) and
    verifies the agent detects BOTH vulnerable JS functions:
      - renderComment    (CWE-79: XSS)
      - getUserByEmail   (CWE-89: SQL Injection)

    Asserts: 100% recall on CWE-79 and CWE-89 for the JS golden dataset.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copy(GOLDEN_JS_FILE, os.path.join(tmpdir, "xss_sqli_sample.js"))
        blocks = TreeSitterParser.extract_code_blocks(tmpdir)
        batches = batch_code_blocks(blocks)
        reviewer = LLMReviewer()
        all_reviews = reviewer.analyze_all_batches(batches)

    findings_by_function: dict[str, list] = {}
    for review in all_reviews:
        findings_by_function.setdefault(review.function_name, []).append(review)

    found_functions = set(findings_by_function.keys())

    assert XSS_FUNCTION in found_functions, (
        f"Agent did NOT flag '{XSS_FUNCTION}' (CWE-79: XSS). "
        f"Functions found: {found_functions}"
    )
    assert SQLI_FUNCTION in found_functions, (
        f"Agent did NOT flag '{SQLI_FUNCTION}' (CWE-89: SQLi). "
        f"Functions found: {found_functions}"
    )

    xss_cwe_ids = {
        cwe[0]
        for r in findings_by_function[XSS_FUNCTION]
        if (cwe := classify_cwe(r.comment))
    }
    assert "CWE-79" in xss_cwe_ids, (
        f"XSS finding in '{XSS_FUNCTION}' was not classified as CWE-79. "
        f"CWEs found: {xss_cwe_ids}."
    )

    sqli_cwe_ids = {
        cwe[0]
        for r in findings_by_function[SQLI_FUNCTION]
        if (cwe := classify_cwe(r.comment))
    }
    assert "CWE-89" in sqli_cwe_ids, (
        f"SQLi finding in '{SQLI_FUNCTION}' was not classified as CWE-89. "
        f"CWEs found: {sqli_cwe_ids}."
    )

    print(f"\n✓ JS XSS detection: {XSS_FUNCTION} flagged and classified as CWE-79")
    print(f"✓ JS SQLi detection: {SQLI_FUNCTION} flagged and classified as CWE-89")
    print(f"✓ {len(all_reviews)} findings across JS golden dataset")
    print("✓ 100% recall on CWE-79 and CWE-89 for multi-language pipeline")
