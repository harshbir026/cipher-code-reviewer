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

from utils.security import scrub_secrets

load_dotenv()
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Pydantic Schema — engineered for OpenAI Structured Outputs compatibility.
# IMPORTANT: No Optional fields, no ge=/le= constraints, no recursive schemas.
# additionalProperties is enforced False automatically by the SDK.
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
    confidence_score: int = Field(
        description=(
            "Integer 0–100 representing the reviewer's epistemic confidence. "
            "Use <80 for subjective, ambiguous, or context-dependent issues. "
            "Use >=80 only when the issue is definitively identifiable from context alone."
        )
    )
    needs_verification: bool = Field(
        description="Must be True if confidence_score is below 80."
    )

    @model_validator(mode="after")
    def clamp_and_sync(self) -> "ReviewComment":
        """
        Post-parse validation:
        1. Clamps confidence_score to [0, 100] range
           (OpenAI Structured Outputs cannot enforce numeric bounds at the schema level).
        2. Ensures needs_verification is always consistent with the score.
        """
        # Clamp the score — fixes the gap in the original blueprint
        self.confidence_score = max(0, min(100, self.confidence_score))
        # Sync the verification flag — overrides any LLM inconsistency
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
# Reviewer
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are an elite, highly critical AI software architect and security auditor \
with 20 years of experience reviewing production Python code. Your reviews are surgical, specific, \
and actionable.

Your task: Analyze the provided Python code blocks and identify genuine bugs, security \
vulnerabilities, performance bottlenecks, and maintainability problems.

Rules:
- Focus on substantive issues. Ignore trivial PEP 8 style nits.
- Every comment must reference the specific function or class name.
- For the confidence_score: assign HIGH confidence (≥80) ONLY when the issue is definitively \
identifiable from the provided code alone. Assign LOW confidence (<80) when:
  * The issue might be acceptable depending on usage context you cannot see
  * The fix requires information from other files not provided
  * The problem is subjective or opinion-based
- Always set needs_verification=True when confidence_score < 80.
- If a code block has no meaningful issues, do not fabricate issues. Simply omit it.
- Provide at least one suggested_fix per comment — never leave it empty.
"""


class LLMReviewer:
    """
    Orchestrates OpenAI API calls using Structured Outputs
    to produce typed, schema-valid code review reports.
    """

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY not found. " "Ensure it is set in your .env file."
            )
        self.client = OpenAI(api_key=api_key)

    def _build_prompt(self, code_blocks: list[dict[str, Any]]) -> str:
        """Assembles the user prompt from a batch of code blocks."""
        context = ""
        for block in code_blocks:
            # Scrub secrets before transmission
            clean_code = scrub_secrets(block["code"])
            context += (
                f"\n---\n"
                f"File: `{block['file_path']}` | "
                f"Line: {block['line_number']} | "
                f"Type: {block['type']} | "
                f"Name: `{block['name']}`\n"
            )
            if block.get("docstring"):
                context += f"Docstring: {block['docstring']}\n"
            context += f"```python\n{clean_code}\n```\n"
        return context

    def analyze_batch(
        self,
        code_blocks: list[dict[str, Any]],
        max_retries: int = 3,
    ) -> CodeReviewReport:
        """
        Sends one batch of code blocks to the LLM and returns a typed report.
        Implements exponential backoff on rate limit errors.
        """
        prompt = self._build_prompt(code_blocks)

        for attempt in range(max_retries):
            try:
                response = self.client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    response_format=CodeReviewReport,
                    temperature=0.2,  # Low temp = analytical consistency
                    max_tokens=2000,
                )
                return response.choices[0].message.parsed

            except RateLimitError:
                wait_time = 2**attempt * 5  # 5s, 10s, 20s
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
        progress_callback=None,
    ) -> list[ReviewComment]:
        """
        Processes all batches sequentially and aggregates results.
        Optionally calls progress_callback(current, total) after each batch.
        """
        all_reviews = []

        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i + 1}/{len(batches)}...")
            try:
                report = self.analyze_batch(batch)
                all_reviews.extend(report.reviews)
            except RuntimeError as e:
                logger.error(f"Batch {i + 1} failed: {e}. Continuing with next batch.")

            if progress_callback:
                progress_callback(i + 1, len(batches))

        return all_reviews
