"""Personalized action-plan generator (one Claude call)."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

from anthropic import Anthropic

from . import config
from .schema import CollegeRow, StudentProfile
from .utils import claude_client, logging_ko


def _read_prompt() -> str:
    return (config.PROMPTS_DIR / "action_plan_system.md").read_text(encoding="utf-8")


def _serialize_picks(rows: list[CollegeRow]) -> list[dict]:
    return [
        {
            "name": r.name,
            "state": r.state,
            "tier": r.tier,
            "adjusted_probability": r.adjusted_probability,
            "has_ed": r.has_ed,
            "has_ea": r.has_ea,
        }
        for r in rows
    ]


def generate_action_plan(
    profile: StudentProfile,
    picks: list[CollegeRow],
    client: Anthropic,
    *,
    save_raw_to: Path | None = None,
) -> str:
    today = _dt.date.today().isoformat()
    user_message = (
        f"## Today's date\n{today}\n\n"
        "## Student profile\n```json\n"
        + json.dumps(profile.model_dump(), ensure_ascii=False, indent=2)
        + "\n```\n\n"
        "## Top picks across all scopes (subset; sorted by tier then probability)\n```json\n"
        + json.dumps(_serialize_picks(picks), ensure_ascii=False, indent=2)
        + "\n```\n\n"
        "Now write the personalized markdown plan as specified in the system prompt. "
        "Output the markdown directly with no preamble."
    )

    system_blocks = [claude_client.make_text_block(_read_prompt())]
    text, _usage = claude_client.call_messages(
        client,
        system_blocks=system_blocks,
        user_message=user_message,
        max_tokens=4096,
        temperature=0.4,
        cache_last_block=False,
        label="Personalized action plan generation",
    )

    if save_raw_to is not None:
        save_raw_to.parent.mkdir(parents=True, exist_ok=True)
        save_raw_to.write_text(text, encoding="utf-8")

    logging_ko.info("Action plan generated")
    return text.strip()
