"""
Security scrubbing utilities.
Strips high-entropy strings and known secret patterns before
transmitting code to external LLM APIs.
"""

import logging
import re

logger = logging.getLogger(__name__)

# Patterns for common secret formats
SECRET_PATTERNS = [
    # OpenAI API keys
    (r"sk-[a-zA-Z0-9]{20,}", "[OPENAI_KEY_REDACTED]"),
    # AWS Access Key IDs
    (r"AKIA[0-9A-Z]{16}", "[AWS_KEY_REDACTED]"),
    # AWS Secret Access Keys (high-entropy 40-char strings after 'secret')
    (
        r"(?i)(aws.{0,20}secret.{0,20})['\"][0-9a-zA-Z/+]{40}['\"]",
        r"\1[AWS_SECRET_REDACTED]",
    ),
    # Generic API keys: variable names containing 'key', 'token', 'secret'
    # followed by an assignment and a quoted string > 20 chars
    (
        r"(?i)(api[_-]?key|token|secret|password|passwd|pwd)\s*=\s*['\"][^'\"]{20,}['\"]",
        r"\1=[REDACTED]",
    ),
    # GitHub tokens
    (r"ghp_[a-zA-Z0-9]{36}", "[GITHUB_TOKEN_REDACTED]"),
    # Generic Bearer tokens in strings
    (r"Bearer\s+[a-zA-Z0-9\-._~+/]{20,}", "Bearer [TOKEN_REDACTED]"),
]


def scrub_secrets(code: str) -> str:
    """
    Apply all secret patterns to a code string and return
    the sanitized version. Logs a warning for each match found.
    """
    scrubbed = code
    for pattern, replacement in SECRET_PATTERNS:
        matches = re.findall(pattern, scrubbed)
        if matches:
            logger.warning(
                f"Secret pattern detected and redacted "
                f"(pattern: {pattern[:30]}...). "
                f"Count: {len(matches)}"
            )
        scrubbed = re.sub(pattern, replacement, scrubbed)
    return scrubbed
