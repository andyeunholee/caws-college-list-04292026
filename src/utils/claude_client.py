"""Thin wrapper around the Anthropic SDK with prompt caching + cost logging."""

from __future__ import annotations

from typing import Any, Optional

from anthropic import Anthropic

from .. import config
from . import logging_ko


def make_client() -> Anthropic:
    api_key = config.require_api_key()
    return Anthropic(api_key=api_key)


def _estimate_cost(usage: dict[str, int]) -> float:
    """Anthropic Sonnet 4.6 pricing (per 1M tokens)."""
    input_tokens = usage.get("input_tokens", 0)
    cw = usage.get("cache_creation_input_tokens", 0)
    cr = usage.get("cache_read_input_tokens", 0)
    out_tokens = usage.get("output_tokens", 0)
    cost = (
        input_tokens / 1_000_000 * config.PRICE_PER_MTOK_INPUT
        + cw / 1_000_000 * config.PRICE_PER_MTOK_CACHE_WRITE
        + cr / 1_000_000 * config.PRICE_PER_MTOK_CACHE_READ
        + out_tokens / 1_000_000 * config.PRICE_PER_MTOK_OUTPUT
    )
    return round(cost, 4)


def call_messages(
    client: Anthropic,
    *,
    system_blocks: list[dict[str, Any]],
    user_message: str,
    max_tokens: int = 8192,
    temperature: float = 0.2,
    cache_last_block: bool = True,
    label: str = "claude",
) -> tuple[str, dict[str, int]]:
    """Send a Messages API call with optional ephemeral caching on the last system block.

    Returns (assistant_text, usage_dict).
    """
    blocks = [dict(b) for b in system_blocks]
    if cache_last_block and blocks:
        # Tag the final system block as ephemeral cache so subsequent calls hit cache.
        blocks[-1] = {**blocks[-1], "cache_control": {"type": "ephemeral"}}

    logging_ko.step(f"Claude 호출: {label} (max_tokens={max_tokens}, streaming)")

    text_parts: list[str] = []
    final_message = None
    with client.messages.stream(
        model=config.CLAUDE_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        system=blocks,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for chunk in stream.text_stream:
            text_parts.append(chunk)
        final_message = stream.get_final_message()

    text = "".join(text_parts)

    usage = {
        "input_tokens": getattr(final_message.usage, "input_tokens", 0),
        "output_tokens": getattr(final_message.usage, "output_tokens", 0),
        "cache_creation_input_tokens": getattr(final_message.usage, "cache_creation_input_tokens", 0) or 0,
        "cache_read_input_tokens": getattr(final_message.usage, "cache_read_input_tokens", 0) or 0,
    }
    logging_ko.cost(usage, _estimate_cost(usage))

    if final_message.stop_reason == "max_tokens":
        logging_ko.warn(f"{label}: 응답이 max_tokens에 도달했습니다. 결과가 잘렸을 수 있습니다.")

    return text, usage


def make_text_block(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}
