"""
Language registry for multi-language parsing.
Maps file extensions to tree-sitter grammars, queries, and code fences.
"""

SUPPORTED_EXTENSIONS = {
    ".py": "python",  # handled by the existing ast-based ASTParser
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}
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

MAX_CODE_LENGTH = 8000
# Captures function declarations, classes, methods, and arrow
# functions/function expressions assigned to a name.
JS_QUERY = """
(function_declaration name: (identifier) @name) @definition.function
(class_declaration name: (identifier) @name) @definition.class
(method_definition name: (property_identifier) @name) @definition.method
(variable_declarator
  name: (identifier) @name
  value: [(arrow_function) (function)]) @definition.function
"""

TS_QUERY = """
(function_declaration name: (identifier) @name) @definition.function
(class_declaration name: (type_identifier) @name) @definition.class
(method_definition name: (property_identifier) @name) @definition.method
(variable_declarator
  name: (identifier) @name
  value: [(arrow_function) (function)]) @definition.function
"""

LANGUAGE_QUERIES = {
    "javascript": JS_QUERY,
    "typescript": TS_QUERY,
    "tsx": TS_QUERY,
}
CODE_FENCE = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "tsx": "tsx",
}
