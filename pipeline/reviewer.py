"""
LLM orchestration module.
Integrates with OpenAI's Structured Outputs API to generate
schema-valid, confidence-rated code review comments.
"""

import logging
import os
import time
from typing import Any, Literal

from dotenv import load_dotenv
from openai import APIError, OpenAI, RateLimitError
from pydantic import BaseModel, Field, model_validator

from pipeline.languages import CODE_FENCE
from utils.security import scrub_secrets

load_dotenv()
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Pydantic Schema
# ─────────────────────────────────────────────


class ReviewComment(BaseModel):
    file_path: str = Field(
        description="Relative path of the file containing the issue."
    )
    function_name: str = Field(
        description="Name of the function or class being reviewed."
    )
    line_number: int = Field(
        description="Approximate line number where the issue occurs."
    )
    issue_category: Literal[
        "Security", "Performance", "Bug", "Style", "Maintainability", "Documentation"
    ] = Field(description="Category of the identified issue.")
    severity: Literal["Low", "Medium", "High", "Critical"] = Field(
        description="Severity of the issue."
    )
    comment: str = Field(description="Specific, actionable description of the issue.")
    suggested_fix: str = Field(
        description="Concrete code-level suggestion to fix the issue."
    )
    vulnerable_snippet: str = Field(
        description=(
            "The specific 1-3 lines of code containing the issue, "
            "extracted verbatim from the function."
        )
    )
    impact: str = Field(
        description=(
            "One sentence explaining the real-world consequence if this "
            "issue is exploited or ignored. Be specific and non-technical. "
            "E.g. 'An attacker could execute arbitrary commands on the server.'"
        )
    )
    confidence_score: int = Field(
        description=(
            "Integer 0-100 representing the reviewer's epistemic confidence. "
            "Use <80 for subjective, ambiguous, or context-dependent issues. "
            "Use >=80 only when the issue is definitively identifiable from context alone."
        )
    )
    needs_verification: bool = Field(
        description="Must be True if confidence_score is below 80."
    )

    @model_validator(mode="after")
    def clamp_and_sync(self) -> "ReviewComment":
        self.confidence_score = max(0, min(100, self.confidence_score))
        self.needs_verification = self.confidence_score < 80
        return self


class CodeReviewReport(BaseModel):
    reviews: list[ReviewComment] = Field(
        description="List of review comments for the submitted code batch."
    )
    batch_summary: str = Field(
        description="One-sentence summary of the overall code quality in this batch."
    )


# ─────────────────────────────────────────────
# System Prompt
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are an elite, highly critical AI software architect and security auditor \
with 20 years of experience reviewing production code across multiple languages. Your reviews \
are surgical, specific, and actionable.

Each code block's header indicates its language — tailor your analysis to that language's \
idioms and vulnerability patterns.

Security patterns to actively detect (flag with HIGH confidence when clearly present):
- SQL Injection (CWE-89): string concatenation/f-strings/template literals building SQL queries;
  raw query methods (e.g. Sequelize/knex .raw(), psycopg2 string formatting) with unsanitized input.
- Cross-Site Scripting / XSS (CWE-79): unescaped user input in HTML output — Python templates
  without autoescape, or JS/TS `innerHTML`, `dangerouslySetInnerHTML`, `document.write` with
  unsanitized input.
- Command Injection (CWE-78): subprocess/os.system with shell=True and variables (Python);
  child_process.exec/execSync with unsanitized input (JS/TS).
- Unsafe Deserialization (CWE-502): pickle.loads on untrusted data (Python); eval() on JSON,
  vm.runInContext, or unsafe JSON.parse reviver misuse (JS/TS).
- Prototype Pollution (CWE-1321, JS/TS only): unguarded merge/assign of user-controlled objects
  into another object (e.g. lodash merge, `obj[key] = value` with attacker-controlled key).

Rules:
- Focus on substantive issues. Ignore trivial PEP 8 style nits.
- Every comment must reference the specific function or class name.
- When flagging SQL Injection, use the phrase "sql injection" in your comment.
- When flagging XSS, use the phrase "xss" or "cross-site scripting" in your comment.
- For the confidence_score: assign HIGH confidence (>=80) ONLY when the issue is definitively \
identifiable from the provided code alone. Assign LOW confidence (<80) when:
  * The issue might be acceptable depending on usage context you cannot see
  * The fix requires information from other files not provided
  * The problem is subjective or opinion-based
- Always set needs_verification=True when confidence_score < 80.
- If a code block has no meaningful issues, do not fabricate issues. Simply omit it.
- Provide at least one suggested_fix per comment — never leave it empty.
"""


# ─────────────────────────────────────────────
# LLM Reviewer Class
# ─────────────────────────────────────────────


class LLMReviewer:
    """
    Orchestrates OpenAI API calls using Structured Outputs
    to produce typed, schema-valid code review reports.
    """

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY not found. Ensure it is set in your .env file."
            )
        self.client = OpenAI(api_key=api_key)

    def _build_prompt(self, code_blocks, call_graph=None):
        prompt_context = ""
        for block in code_blocks:
            clean_code = scrub_secrets(block["code"])
            language = block.get("language", "python")
            fence = CODE_FENCE.get(language, "text")
            prompt_context += (
                f"\n---\n"
                f"File: `{block['file_path']}` | "
                f"Language: {language} | "
                f"Line: {block['line_number']} | "
                f"Type: {block['type']} | "
                f"Name: `{block['name']}`\n"
            )
            if block.get("docstring"):
                prompt_context += f"Docstring: {block['docstring']}\n"
            if call_graph and block["name"] in call_graph:
                callers = [
                    fn for fn, calls in call_graph.items() if block["name"] in calls
                ]
                callees = call_graph.get(block["name"], [])
                if callers:
                    prompt_context += f"Called by: {', '.join(callers[:5])}\n"
                if callees:
                    prompt_context += f"Calls: {', '.join(callees[:10])}\n"
            prompt_context += f"```{fence}\n{clean_code}\n```\n"
        return prompt_context

    def analyze_batch(
        self,
        code_blocks: list[dict[str, Any]],
        call_graph: dict[str, list[str]] = None,
        max_retries: int = 3,
    ) -> CodeReviewReport:
        """
        Sends one batch of code blocks to the LLM and returns a typed report.
        Implements exponential backoff on rate limit errors.
        """
        prompt = self._build_prompt(code_blocks, call_graph)

        for attempt in range(max_retries):
            try:
                response = self.client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    response_format=CodeReviewReport,
                    temperature=0.2,
                    max_tokens=4000,
                )
                return response.choices[0].message.parsed

            except RateLimitError:
                wait_time = 2**attempt * 5
                logger.warning(
                    f"Rate limit hit. Retrying in {wait_time}s "
                    f"(attempt {attempt + 1}/{max_retries})..."
                )
                time.sleep(wait_time)

            except APIError as e:
                logger.error(f"OpenAI API error: {e}")
                raise RuntimeError(f"LLM API call failed: {e}") from e

        raise RuntimeError(
            f"LLM call failed after {max_retries} retries due to rate limiting."
        )

    def analyze_all_batches(
        self,
        batches: list[list[dict[str, Any]]],
        call_graph: dict[str, list[str]] = None,
        progress_callback=None,
    ) -> list[ReviewComment]:
        """Processes all batches and aggregates results."""
        all_reviews = []
        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i + 1}/{len(batches)}...")
            try:
                report = self.analyze_batch(batch, call_graph)
                all_reviews.extend(report.reviews)
            except RuntimeError as e:
                logger.error(f"Batch {i + 1} failed: {e}. Continuing.")
            if progress_callback:
                progress_callback(i + 1, len(batches))
        return all_reviews


# ─────────────────────────────────────────────
# Module-level utility functions
# These are OUTSIDE the class — importable directly
# ─────────────────────────────────────────────


def compute_health_score(
    reviews: list,
    feedback: dict = None,
) -> dict:
    """
    Computes repository health score 0-100.
    Excludes false positives from penalty calculation.
    """
    if not reviews:
        return {"score": 100, "grade": "A", "color": "#22C55E"}

    severity_weights = {"Critical": 25, "High": 10, "Medium": 4, "Low": 1}
    penalty = 0

    for review in reviews:
        key = f"{review.file_path}_{review.function_name}" f"_{review.line_number}"
        if feedback and feedback.get(key) == "false_positive":
            continue
        weight = severity_weights.get(review.severity, 1)
        confidence_multiplier = review.confidence_score / 100
        penalty += weight * confidence_multiplier

    score = max(0, 100 - min(penalty, 100))

    if score >= 90:
        grade, color = "A", "#22C55E"
    elif score >= 75:
        grade, color = "B", "#84CC16"
    elif score >= 60:
        grade, color = "C", "#F5A623"
    elif score >= 40:
        grade, color = "D", "#F97316"
    else:
        grade, color = "F", "#EF4444"

    return {"score": round(score), "grade": grade, "color": color}


CWE_MAPPING = {
    # CWE-89: SQL Injection — multiple keyword variants
    "sql injection": ("CWE-89", "https://cwe.mitre.org/data/definitions/89.html"),
    "sqli": ("CWE-89", "https://cwe.mitre.org/data/definitions/89.html"),
    "sql query construction": (
        "CWE-89",
        "https://cwe.mitre.org/data/definitions/89.html",
    ),
    "parameterized quer": ("CWE-89", "https://cwe.mitre.org/data/definitions/89.html"),
    # CWE-79: Cross-Site Scripting
    "xss": ("CWE-79", "https://cwe.mitre.org/data/definitions/79.html"),
    "cross-site scripting": (
        "CWE-79",
        "https://cwe.mitre.org/data/definitions/79.html",
    ),
    "cross site scripting": (
        "CWE-79",
        "https://cwe.mitre.org/data/definitions/79.html",
    ),
    "html injection": ("CWE-79", "https://cwe.mitre.org/data/definitions/79.html"),
    "html escaping": ("CWE-79", "https://cwe.mitre.org/data/definitions/79.html"),
    # CWE-78: Command Injection
    "command injection": ("CWE-78", "https://cwe.mitre.org/data/definitions/78.html"),
    "shell": ("CWE-78", "https://cwe.mitre.org/data/definitions/78.html"),
    # CWE-502: Unsafe Deserialization
    "pickle": ("CWE-502", "https://cwe.mitre.org/data/definitions/502.html"),
    "deserialization": ("CWE-502", "https://cwe.mitre.org/data/definitions/502.html"),
    # CWE-22: Path Traversal
    "path traversal": ("CWE-22", "https://cwe.mitre.org/data/definitions/22.html"),
    # CWE-798: Hardcoded Credentials
    "hardcoded credential": (
        "CWE-798",
        "https://cwe.mitre.org/data/definitions/798.html",
    ),
    "hardcoded password": (
        "CWE-259",
        "https://cwe.mitre.org/data/definitions/259.html",
    ),
    # CWE-352: CSRF
    "csrf": ("CWE-352", "https://cwe.mitre.org/data/definitions/352.html"),
    # CWE-120: Buffer Overflow
    "buffer overflow": ("CWE-120", "https://cwe.mitre.org/data/definitions/120.html"),
    # CWE-362: Race Condition
    "race condition": ("CWE-362", "https://cwe.mitre.org/data/definitions/362.html"),
    # CWE-476: Null Pointer
    "null pointer": ("CWE-476", "https://cwe.mitre.org/data/definitions/476.html"),
    # CWE-369: Division by Zero
    "division by zero": ("CWE-369", "https://cwe.mitre.org/data/definitions/369.html"),
    # CWE-601: Open Redirect
    "open redirect": ("CWE-601", "https://cwe.mitre.org/data/definitions/601.html"),
    # CWE-327: Weak Cryptography
    "weak cryptography": ("CWE-327", "https://cwe.mitre.org/data/definitions/327.html"),
    "insecure random": ("CWE-330", "https://cwe.mitre.org/data/definitions/330.html"),
    # CWE-95: Code Injection
    "eval": ("CWE-95", "https://cwe.mitre.org/data/definitions/95.html"),
    "exec": ("CWE-95", "https://cwe.mitre.org/data/definitions/95.html"),
}


def classify_cwe(comment: str) -> tuple[str, str] | None:
    """
    Maps a review comment to a CWE classification based on keyword matching.
    Returns (CWE-ID, URL) or None.
    """
    comment_lower = comment.lower()
    for keyword, (cwe_id, url) in CWE_MAPPING.items():
        if keyword in comment_lower:
            return cwe_id, url
    return None
