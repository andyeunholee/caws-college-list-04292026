"""Translate dynamic Claude-generated content (action plan markdown) into Korean.

Static UI strings are handled by src.i18n. This module covers anything Claude
itself produced in English that needs to surface in the Korean Word file.
"""

from __future__ import annotations

from pathlib import Path

from anthropic import Anthropic

from .utils import claude_client, logging_ko


_TRANSLATE_SYSTEM = """You are a professional translator specializing in U.S. college admissions counseling.

The user will give you a Markdown document written in English by an admissions counselor for a Korean-speaking parent or student. Translate it into natural, professional Korean while preserving:

1. **All Markdown structure** — headings (##, ###), bullet lists (-, *), numbered lists (1., 2.), bold (**text**), and paragraph breaks. Output the same markdown structure, just with Korean prose.
2. **Proper nouns in their original form** — keep college names, person names, and place names in English (e.g., "Johns Hopkins University", "Yena", "Suwanee, GA"). Do NOT transliterate into Hangul.
3. **Numbers, dates, and scores verbatim** — SAT scores (1480), GPA (3.96), dates (September 12, 2026), percentages (12%), section names (EBRW, Math) stay in their original form.
4. **Domain abbreviations** — keep ED, EA, REA, SCEA, RD, AP, IB, DE, HOSA, HPAC, MCAT, QuestBridge, FAFSA, CSS Profile in English. Do NOT translate them.
5. **Inline em dashes (—) and bullet conventions** stay as-is.

Style: warm but direct counselor tone, like a Korean college counselor speaking to a parent. Use polite-formal speech style (해요체 + ~합니다 mix as appropriate, default to ~합니다 for headings/structure, ~해요 for advice). Avoid over-literal English-to-Korean translations; rephrase for natural Korean reading flow.

Output ONLY the translated markdown. No preamble. No closing remark. No code fences."""


def translate_markdown_to_korean(
    en_markdown: str,
    client: Anthropic,
    *,
    save_to: Path | None = None,
    label: str = "마크다운 한글 번역",
) -> str:
    """Translate an English markdown document into Korean via Claude Sonnet."""

    if save_to is not None and save_to.exists():
        cached = save_to.read_text(encoding="utf-8").strip()
        if cached:
            logging_ko.info(f"[cache] 한글 번역 재사용: {save_to.name}")
            return cached

    system_blocks = [claude_client.make_text_block(_TRANSLATE_SYSTEM)]
    text, _usage = claude_client.call_messages(
        client,
        system_blocks=system_blocks,
        user_message=en_markdown,
        max_tokens=24000,
        temperature=0.2,
        cache_last_block=False,  # short system; no benefit
        label=label,
    )
    translated = text.strip()
    if translated.startswith("```"):
        # Strip accidental fences
        lines = translated.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        translated = "\n".join(lines).strip()

    if save_to is not None:
        save_to.parent.mkdir(parents=True, exist_ok=True)
        save_to.write_text(translated, encoding="utf-8")
        logging_ko.info(f"한글 번역 저장: {save_to.name}")

    return translated
