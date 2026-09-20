"""Parse and log Responses usage for live cost visibility."""

from __future__ import annotations

import logging
import os

from .constants import (
    SOL_CACHE_WRITE_USD_PER_MILLION,
    SOL_CACHED_INPUT_USD_PER_MILLION,
    SOL_INPUT_USD_PER_MILLION,
    SOL_OUTPUT_USD_PER_MILLION,
)
from .models.open_ai_models import ResponsesResult

LOGGER = logging.getLogger(__name__)

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_BLUE = "\033[34m"
_RED = "\033[31m"

_COLUMN_GAP = "  "


def estimate_sol_short_context_usd(
    input_tokens: int,
    cached_tokens: int,
    output_tokens: int,
    cache_write_tokens: int = 0,
) -> float:
    """Estimate USD using gpt-5.6-sol short-context published rates.

    `output_tokens` already includes reasoning tokens. Do not add reasoning
    again. `cached_tokens` and `cache_write_tokens` are portions of
    `input_tokens`, not extra.
    """
    uncached_input = max(input_tokens - cached_tokens - cache_write_tokens, 0)
    return (
        uncached_input * SOL_INPUT_USD_PER_MILLION / 1_000_000
        + cached_tokens * SOL_CACHED_INPUT_USD_PER_MILLION / 1_000_000
        + cache_write_tokens * SOL_CACHE_WRITE_USD_PER_MILLION / 1_000_000
        + output_tokens * SOL_OUTPUT_USD_PER_MILLION / 1_000_000
    )


def format_responses_usage(
    *,
    model: str,
    chat_id: str,
    input_tokens: int | None = None,
    cached_tokens: int | None = None,
    cache_write_tokens: int | None = None,
    output_tokens: int | None = None,
    reasoning_tokens: int | None = None,
    estimated_cost_usd: float | None = None,
) -> str:
    """Build a coloured, column-aligned usage block for container logs."""
    rows: list[tuple[str, str, str]] = [
        ("chat_id", chat_id, "meta"),
        ("model", model, "meta"),
    ]
    if input_tokens is None:
        rows.append(("usage", "missing", "alert"))
    else:
        rows.extend(
            [
                ("input tokens", f"{input_tokens:,}", "tokens"),
                ("cached tokens", f"{cached_tokens or 0:,}", "tokens"),
                ("cache write tokens", f"{cache_write_tokens or 0:,}", "tokens"),
                ("output tokens", f"{output_tokens or 0:,}", "tokens"),
                ("reasoning tokens", f"{reasoning_tokens or 0:,}", "tokens"),
                ("estimated cost", f"${estimated_cost_usd or 0:.6f}", "cost"),
            ]
        )

    label_width = max(len(label) for label, _value, _kind in rows)
    value_width = max(len(value) for _label, value, _kind in rows)

    lines = [_style("OpenAI usage", _BOLD, _CYAN)]
    for label, value, kind in rows:
        padded_label = label.ljust(label_width)
        padded_value = value.rjust(value_width)
        lines.append(
            f"  {_style(padded_label, _CYAN)}{_COLUMN_GAP}"
            f"{_style(padded_value, *_value_style(kind))}"
        )
    if input_tokens is not None:
        lines.append(_style("  gpt-5.6-sol short-context rates", _DIM))
    return "\n".join(lines)


def log_responses_usage(
    result: ResponsesResult,
    *,
    model: str,
    chat_id: str,
) -> None:
    """Log token counts and a Sol short-context USD estimate for one HTTP call."""
    usage = result.usage
    if usage is None:
        LOGGER.info(format_responses_usage(model=model, chat_id=chat_id))
        return

    estimated_cost_usd = estimate_sol_short_context_usd(
        usage.input_tokens,
        usage.cached_tokens,
        usage.output_tokens,
        usage.cache_write_tokens,
    )
    LOGGER.info(
        format_responses_usage(
            model=model,
            chat_id=chat_id,
            input_tokens=usage.input_tokens,
            cached_tokens=usage.cached_tokens,
            cache_write_tokens=usage.cache_write_tokens,
            output_tokens=usage.output_tokens,
            reasoning_tokens=usage.reasoning_tokens,
            estimated_cost_usd=estimated_cost_usd,
        )
    )


def _colour_enabled() -> bool:
    """Colour Docker Desktop logs by default; honour NO_COLOR."""
    no_color = os.environ.get("NO_COLOR")
    return not (no_color is not None and no_color != "")


def _style(text: str, *codes: str) -> str:
    if not _colour_enabled() or not codes:
        return text
    return f"{''.join(codes)}{text}{_RESET}"


def _value_style(kind: str) -> tuple[str, ...]:
    if kind == "cost":
        return (_BOLD, _GREEN)
    if kind == "tokens":
        return (_BLUE,)
    if kind == "alert":
        return (_BOLD, _RED)
    return (_BLUE,)
