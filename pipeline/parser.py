"""
AST-based code parsing module.
Extracts function and class definitions from Python source files
as discrete semantic units for LLM analysis.
"""

import ast
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Directories to skip during file traversal
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    ".tox",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
    ".pytest_cache",
    ".mypy_cache",
}

# Maximum source code length per block sent to LLM (characters)
# Prevents single massive functions from blowing the token budget
MAX_CODE_LENGTH = 8000


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
