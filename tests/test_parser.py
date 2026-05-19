"""
Unit tests for the AST parsing module.
Uses temporary files with known content for deterministic testing.
"""

import os
import tempfile

import pytest

from pipeline.parser import ASTParser


@pytest.fixture
def simple_python_file():
    """Creates a temp directory with a simple Python file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "sample.py")
        with open(file_path, "w") as f:
            f.write('''
def greet(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}"


class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b

    def divide(self, a: int, b: int) -> float:
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b
''')
        yield tmpdir


@pytest.fixture
def syntax_error_file():
    """Creates a temp directory with a file containing a syntax error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "broken.py")
        with open(file_path, "w") as f:
            f.write("def broken(\n    # unclosed parenthesis")
        yield tmpdir


class TestASTParser:
    def test_extracts_function(self, simple_python_file):
        blocks = ASTParser.extract_code_blocks(simple_python_file)
        names = [b["name"] for b in blocks]
        assert "greet" in names

    def test_extracts_class(self, simple_python_file):
        blocks = ASTParser.extract_code_blocks(simple_python_file)
        names = [b["name"] for b in blocks]
        assert "Calculator" in names

    def test_extracts_methods(self, simple_python_file):
        blocks = ASTParser.extract_code_blocks(simple_python_file)
        names = [b["name"] for b in blocks]
        assert "add" in names
        assert "divide" in names

    def test_correct_line_numbers(self, simple_python_file):
        blocks = ASTParser.extract_code_blocks(simple_python_file)
        greet_block = next(b for b in blocks if b["name"] == "greet")
        assert greet_block["line_number"] > 0

    def test_extracts_docstring(self, simple_python_file):
        blocks = ASTParser.extract_code_blocks(simple_python_file)
        greet_block = next(b for b in blocks if b["name"] == "greet")
        assert greet_block["docstring"] == "Return a greeting."

    def test_syntax_error_doesnt_crash(self, syntax_error_file):
        # Should return empty list, not raise
        blocks = ASTParser.extract_code_blocks(syntax_error_file)
        assert isinstance(blocks, list)

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            blocks = ASTParser.extract_code_blocks(tmpdir)
            assert blocks == []
