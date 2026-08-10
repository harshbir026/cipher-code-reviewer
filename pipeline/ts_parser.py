"""
Tree-sitter based parser for non-Python languages.
Produces the same dict shape as ASTParser so the rest of the
pipeline doesn't need to know which language a block came from.
"""

import logging
import os
from typing import Any

from tree_sitter_languages import get_language, get_parser

from pipeline.languages import (
    IGNORED_DIRS,
    LANGUAGE_QUERIES,
    MAX_CODE_LENGTH,
    SUPPORTED_EXTENSIONS,
)

logger = logging.getLogger(__name__)

_PARSER_CACHE: dict = {}
_QUERY_CACHE: dict = {}


def _get_parser(language: str):
    if language not in _PARSER_CACHE:
        _PARSER_CACHE[language] = get_parser(language)
    return _PARSER_CACHE[language]


def _get_query(language: str):
    if language not in _QUERY_CACHE:
        lang_obj = get_language(language)
        _QUERY_CACHE[language] = lang_obj.query(LANGUAGE_QUERIES[language])
    return _QUERY_CACHE[language]


class TreeSitterParser:
    @staticmethod
    def extract_code_blocks(repo_path: str) -> list[dict[str, Any]]:
        extracted_blocks = []

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [
                d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")
            ]

            for file in files:
                ext = os.path.splitext(file)[1]
                language = SUPPORTED_EXTENSIONS.get(ext)
                if language is None or language == "python":
                    continue  # python stays with ASTParser

                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repo_path)

                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        source = f.read()
                    if not source.strip():
                        continue

                    source_bytes = source.encode("utf-8")
                    parser = _get_parser(language)
                    tree = parser.parse(source_bytes)
                    query = _get_query(language)

                    seen_spans = set()
                    captures = query.captures(tree.root_node)
                    # group captures by their parent definition node
                    for node, capture_name in captures:
                        if not capture_name.startswith("definition."):
                            continue

                        span = (node.start_byte, node.end_byte)
                        if span in seen_spans:
                            continue
                        seen_spans.add(span)

                        name_node = next(
                            (c for c, cname in query.captures(node) if cname == "name"),
                            None,
                        )
                        name = (
                            source_bytes[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf-8")
                            if name_node
                            else "<anonymous>"
                        )

                        code_segment = source_bytes[
                            node.start_byte : node.end_byte
                        ].decode("utf-8")
                        if len(code_segment) > MAX_CODE_LENGTH:
                            code_segment = (
                                code_segment[:MAX_CODE_LENGTH]
                                + "\n// ... [truncated — block exceeds max length]"
                            )

                        extracted_blocks.append(
                            {
                                "file_path": relative_path,
                                "name": name,
                                "type": capture_name.split(".")[-1],
                                "line_number": node.start_point[0] + 1,
                                "code": code_segment,
                                "docstring": None,
                                "language": language,
                            }
                        )

                except Exception as e:
                    logger.warning(
                        f"Tree-sitter parse failed for {relative_path}: {e} — skipping."
                    )

        return extracted_blocks
