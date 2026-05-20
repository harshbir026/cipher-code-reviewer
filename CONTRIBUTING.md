# Contributing to CIPHER

## Adding a New Language
To add support for a new language beyond Python:
1. Create a new parser in `pipeline/` (e.g., `js_parser.py`)
2. Use tree-sitter for non-Python languages
3. Register the parser in `pipeline/parser.py` based on file extension

## Adding a New LLM Provider
The reviewer is provider-agnostic at the schema level.
To add Claude or Gemini support:
1. Implement a new client in `pipeline/reviewer.py`
2. Keep the same `CodeReviewReport` Pydantic schema
3. Add provider selection to the sidebar

## Running Tests
pytest tests/ -v

## Code Style
This project uses Ruff for linting and formatting.
pre-commit install