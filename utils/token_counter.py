"""
Token counting utilities using tiktoken.
Ensures code batches stay within safe LLM context window limits.
"""

import logging

import tiktoken

logger = logging.getLogger(__name__)

# GPT-4o-mini uses the cl100k_base encoding
ENCODING = tiktoken.get_encoding("cl100k_base")

# Leave headroom for system prompt (~500 tokens) and response (~1000 tokens)
# gpt-4o-mini has a 128k context window; we batch at 3000 tokens for safety
MAX_TOKENS_PER_BATCH = 3000


def count_tokens(text: str) -> int:
    """Returns the number of tokens in a string."""
    return len(ENCODING.encode(text))


def batch_code_blocks(
    code_blocks: list[dict],
    max_tokens: int = MAX_TOKENS_PER_BATCH,
) -> list[list[dict]]:
    """
    Splits a list of code blocks into batches where each batch's
    combined token count stays under max_tokens.

    Returns a list of batches, where each batch is a list of code block dicts.
    """
    batches = []
    current_batch = []
    current_token_count = 0

    for block in code_blocks:
        # Build the text representation of this block as it will appear in the prompt
        block_text = (
            f"\nFile: {block['file_path']} | "
            f"Line: {block['line_number']} | "
            f"Function: {block['name']}\n"
            f"```python\n{block['code']}\n```\n"
        )
        block_tokens = count_tokens(block_text)

        # If a single block exceeds the budget, send it alone (already truncated by parser)
        if block_tokens > max_tokens:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_token_count = 0
            batches.append([block])
            continue

        # If adding this block would overflow the batch, finalize and start new batch
        if current_token_count + block_tokens > max_tokens:
            batches.append(current_batch)
            current_batch = [block]
            current_token_count = block_tokens
        else:
            current_batch.append(block)
            current_token_count += block_tokens

    # Don't forget the last partial batch
    if current_batch:
        batches.append(current_batch)

    logger.info(
        f"Batching complete: {len(code_blocks)} blocks → {len(batches)} batches."
    )
    return batches
