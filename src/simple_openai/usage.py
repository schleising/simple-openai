"""Parse and log Responses usage for live cost visibility."""

import logging

from .constants import (
    SOL_CACHED_INPUT_USD_PER_MILLION,
    SOL_INPUT_USD_PER_MILLION,
    SOL_OUTPUT_USD_PER_MILLION,
)
from .models.open_ai_models import ResponsesResult

LOGGER = logging.getLogger(__name__)


def estimate_sol_short_context_usd(
    input_tokens: int,
    cached_tokens: int,
    output_tokens: int,
) -> float:
    """Estimate USD using gpt-5.6-sol short-context published rates.

    `output_tokens` already includes reasoning tokens. Do not add reasoning
    again.
    """
    uncached_input = max(input_tokens - cached_tokens, 0)
    return (
        uncached_input * SOL_INPUT_USD_PER_MILLION / 1_000_000
        + cached_tokens * SOL_CACHED_INPUT_USD_PER_MILLION / 1_000_000
        + output_tokens * SOL_OUTPUT_USD_PER_MILLION / 1_000_000
    )


def log_responses_usage(
    result: ResponsesResult,
    *,
    model: str,
    chat_id: str,
) -> None:
    """Log token counts and a Sol short-context USD estimate for one HTTP call."""
    usage = result.usage
    if usage is None:
        LOGGER.info("OpenAI usage missing chat_id=%s model=%s", chat_id, model)
        return

    estimated_cost_usd = estimate_sol_short_context_usd(
        usage.input_tokens,
        usage.cached_tokens,
        usage.output_tokens,
    )
    LOGGER.info(
        "OpenAI usage chat_id=%s model=%s input_tokens=%s cached_tokens=%s "
        "output_tokens=%s reasoning_tokens=%s estimated_cost_usd=%.6f "
        "(gpt-5.6-sol short-context rates)",
        chat_id,
        model,
        usage.input_tokens,
        usage.cached_tokens,
        usage.output_tokens,
        usage.reasoning_tokens,
        estimated_cost_usd,
    )
