"""Raw email text → StudentProfile via Claude Sonnet (JSON-only output)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from anthropic import Anthropic
from pydantic import ValidationError

from . import config
from .schema import StudentProfile
from .utils import claude_client, logging_ko


def _read_prompt() -> str:
    return (config.PROMPTS_DIR / "extraction_system.md").read_text(encoding="utf-8")


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json_object(text: str) -> str:
    """Pull the first balanced JSON object out of the response text."""
    text = text.strip()
    if text.startswith("```"):
        # Strip markdown fences if Claude wrapped the response.
        text = re.sub(r"^```(?:json)?", "", text).strip()
        if text.endswith("```"):
            text = text[: -3].strip()
    match = _JSON_OBJECT_RE.search(text)
    if not match:
        raise ValueError("응답에서 JSON 객체를 찾지 못했습니다.")
    return match.group(0)


def extract_profile(raw_text: str, client: Anthropic) -> StudentProfile:
    """Extract a StudentProfile from a free-form pasted email."""

    system_blocks = [claude_client.make_text_block(_read_prompt())]

    last_error: str | None = None
    for attempt in range(2):
        user_message = raw_text if attempt == 0 else (
            "Previous attempt failed validation: "
            f"{last_error}\n\nRe-extract from the same email below and output ONLY valid JSON.\n\n"
            + raw_text
        )

        text, _usage = claude_client.call_messages(
            client,
            system_blocks=system_blocks,
            user_message=user_message,
            max_tokens=4096,
            temperature=0.0,
            cache_last_block=False,  # extraction prompt is short; not worth caching across runs
            label=f"학생 정보 추출 (시도 {attempt + 1})",
        )

        try:
            payload = json.loads(_extract_json_object(text))
            profile = StudentProfile.model_validate(payload)
            logging_ko.info(f"학생 이름: {profile.name} / 주: {profile.state or '미상'}")
            return profile
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            last_error = str(e)
            logging_ko.warn(f"추출 결과 검증 실패: {last_error}")

    raise RuntimeError(f"학생 프로필 추출 실패. 마지막 오류: {last_error}")


def save_profile(profile: StudentProfile, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(profile.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logging_ko.info(f"학생 프로필 저장: {out_path}")


def load_profile(path: Path) -> StudentProfile:
    data = json.loads(path.read_text(encoding="utf-8"))
    return StudentProfile.model_validate(data)
