"""
AST-based code parsing module.
Extracts function and class definitions from Python source files
as discrete semantic units for LLM analysis.
"""

import ast
import logging
import os
from typing import Any

from pipeline.languages import IGNORED_DIRS, MAX_CODE_LENGTH
from pipeline.ts_parser import TreeSitterParser

logger = logging.getLogger(__name__)


class ASTParser:
    """
    Parses Python files and extracts named code blocks
    (functions and classes) as structured dictionaries.
    """

    @staticmethod
    def extract_code_blocks(repo_path: str) -> list[dict[str, Any]]:
        """
        Walks the repository and extracts all FunctionDef and ClassDef nodes.

        Returns a list of dicts, each containing:
        - file_path: relative path from repo root
        - name: function or class name
        - type: 'FunctionDef', 'AsyncFunctionDef', or 'ClassDef'
        - line_number: starting line in the source file
        - code: the raw source string for the node
        - docstring: the docstring if present, else None
        """
        extracted_blocks = []
        python_files_found = 0
        python_files_parsed = 0

        for root, dirs, files in os.walk(repo_path):
            # Modify dirs in-place to skip ignored directories
            # This prevents os.walk from descending into them
            dirs[:] = [
                d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")
            ]

            for file in files:
                if not file.endswith(".py"):
                    continue

                python_files_found += 1
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repo_path)

                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        source = f.read()

                    # Skip empty files
                    if not source.strip():
                        continue

                    tree = ast.parse(source, filename=relative_path)
                    python_files_parsed += 1

                    for node in ast.walk(tree):
                        if not isinstance(
                            node,
                            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                        ):
                            continue

                        # Skip private/dunder methods for brevity
                        # (configurable — remove this filter if you want them)
                        if node.name.startswith("__") and node.name.endswith("__"):
                            # Keep __init__ — it's architecturally important
                            if node.name != "__init__":
                                continue

                        code_segment = ast.get_source_segment(source, node)
                        if not code_segment:
                            continue

                        # Truncate extremely long functions
                        if len(code_segment) > MAX_CODE_LENGTH:
                            code_segment = (
                                code_segment[:MAX_CODE_LENGTH]
                                + "\n    # ... [truncated — function exceeds max length]"
                            )

                        # Extract docstring if present
                        docstring = ast.get_docstring(node)

                        extracted_blocks.append(
                            {
                                "file_path": relative_path,
                                "name": node.name,
                                "type": type(node).__name__,
                                "line_number": node.lineno,
                                "code": code_segment,
                                "docstring": docstring,
                                "language": "python",
                            }
                        )

                except SyntaxError as e:
                    logger.warning(
                        f"SyntaxError in {relative_path} at line {e.lineno}: "
                        f"{e.msg} — skipping file."
                    )
                except UnicodeDecodeError:
                    logger.warning(
                        f"UnicodeDecodeError in {relative_path} — skipping file."
                    )
                except Exception as e:
                    logger.warning(
                        f"Unexpected error parsing {relative_path}: {e} — skipping."
                    )

        logger.info(
            f"Parsing complete: {python_files_parsed}/{python_files_found} "
            f"files parsed, {len(extracted_blocks)} code blocks extracted."
        )

        return extracted_blocks


def build_call_graph(repo_path: str) -> dict[str, list[str]]:
    """
    Builds a simple call graph: maps each function name
    to the list of functions it calls.
    Used to provide cross-file context to the LLM.
    """
    call_graph = {}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".") and d not in {"venv", "__pycache__"}
        ]
        for file in files:
            if not file.endswith(".py"):
                continue
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    source = f.read()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        calls = []
                        for child in ast.walk(node):
                            if isinstance(child, ast.Call):
                                if isinstance(child.func, ast.Name):
                                    calls.append(child.func.id)
                                elif isinstance(child.func, ast.Attribute):
                                    calls.append(child.func.attr)
                        call_graph[node.name] = calls
            except Exception:
                continue

    return call_graph


def extract_all_code_blocks(repo_path: str) -> list[dict[str, Any]]:
    """Extracts code blocks across all supported languages."""

    blocks = ASTParser.extract_code_blocks(repo_path)
    blocks.extend(TreeSitterParser.extract_code_blocks(repo_path))
    return blocks
