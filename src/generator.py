"""3-scope tiered college list generator with prompt caching.

Each scope makes 3 sub-calls (one per tier) so each Claude response is small enough
to fit comfortably under max_tokens. The cached system block is shared across all
9 sub-calls (3 scopes × 3 tiers) so cache hits dominate after the first call.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from pydantic import ValidationError

from . import config
from .schema import CollegeFact, CollegeRow, Scope, StudentProfile, Tier, TieredList
from .utils import claude_client, logging_ko


_SCOPE_LABELS: dict[Scope, str] = {
    "national_excl_home": "전국 (LAC 제외, 학생 거주 주 제외)",
    "in_state": "거주 주 4년제 대학 (LAC 제외)",
    "lac": "전국 Liberal Arts College",
}

_TIER_BANDS: dict[Tier, str] = {
    "reach": "Reach (adjusted_probability < 0.25)",
    "match": "Match (0.25 ≤ adjusted_probability < 0.60)",
    "safety": "Safety (adjusted_probability ≥ 0.60)",
}


def _read_prompt(name: str) -> str:
    return (config.PROMPTS_DIR / name).read_text(encoding="utf-8")


def _grounding_to_jsonable(facts: list[CollegeFact]) -> list[dict[str, Any]]:
    return [
        {
            "name": f.name,
            "state": f.state,
            "is_lac": f.is_lac,
            "acceptance_rate": f.acceptance_rate,
            "sat_total": f.sat_total,
            "act_midpoint": f.act_midpoint,
            "has_ed": f.has_ed,
            "has_ea": f.has_ea,
            "has_rea": f.has_rea,
            "ed_deadline": f.ed_deadline,
            "ea_deadline": f.ea_deadline,
            "rea_deadline": f.rea_deadline,
            "test_policy": f.test_policy,
            "early_acceptance_rate": f.early_acceptance_rate,
        }
        for f in facts
    ]


def _build_system_blocks(grounding_subset: list[CollegeFact]) -> list[dict[str, Any]]:
    persona = _read_prompt("generation_system.md")
    calibration = _read_prompt("probability_calibration.md")
    grounding_json = json.dumps(_grounding_to_jsonable(grounding_subset), ensure_ascii=False)
    big_block = (
        f"{persona}\n\n---\n\n{calibration}\n\n---\n\n"
        "# Authoritative grounding facts for this scope\n\n"
        "Treat the following JSON array as a high-confidence source for the colleges listed. "
        "Use the values as-is unless you have strong reason otherwise. For colleges not in this "
        "array, use your training knowledge but be conservative.\n\n"
        f"```json\n{grounding_json}\n```\n"
    )
    return [claude_client.make_text_block(big_block)]


_SCOPE_DIRECTIVE: dict[Scope, str] = {
    "national_excl_home": (
        "Scope: **National universities, excluding the student's home state and excluding "
        "all Liberal Arts Colleges.**"
    ),
    "in_state": (
        "Scope: **4-year colleges in the student's home state, excluding all Liberal Arts "
        "Colleges.** If fewer real colleges exist in this tier than the target count, output "
        "as many as realistically exist; do NOT invent."
    ),
    "lac": (
        "Scope: **Liberal Arts Colleges nationwide** (in-state and out-of-state both allowed)."
    ),
}


def _tier_user_message(
    scope: Scope, tier: Tier, profile: StudentProfile, target_count: int
) -> str:
    profile_json = json.dumps(profile.model_dump(), ensure_ascii=False, indent=2)
    home_state = profile.state or "UNKNOWN"
    home_filter = (
        f"Exclude any college whose state == \"{home_state}\". " if scope == "national_excl_home" else ""
    )
    in_state_filter = (
        f"Include only colleges located in state \"{home_state}\". "
        if scope == "in_state" else ""
    )
    return (
        "## Student profile\n```json\n"
        f"{profile_json}\n"
        "```\n\n"
        f"## Task\n{_SCOPE_DIRECTIVE[scope]} {home_filter}{in_state_filter}\n\n"
        f"Produce the **{tier.upper()}** tier only — colleges whose profile-adjusted "
        f"probability puts them in this band: {_TIER_BANDS[tier]}.\n\n"
        f"Target count: {target_count} colleges. If the realistic universe is smaller, "
        "output as many real colleges as exist; do NOT pad with fictitious schools.\n\n"
        "Output ONLY a JSON array (no surrounding object, no prose, no fences). "
        "Each element must match the CollegeRow schema with `tier` set to "
        f"\"{tier}\". Sort the array by adjusted_probability ascending."
    )


# ────────────────────── parsing & salvage ──────────────────────


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    return text


def _salvage_array(text: str) -> list[dict[str, Any]]:
    """Extract every complete `{...}` object from a (possibly truncated) JSON array."""
    cleaned = _strip_fences(text)
    start = cleaned.find("[")
    if start == -1:
        # Maybe model returned an object with a key — try that.
        obj_start = cleaned.find("{")
        if obj_start == -1:
            return []
        # Treat the whole thing as a hopefully-parseable object containing one array.
        try:
            obj = json.loads(cleaned[obj_start:])
            for v in obj.values():
                if isinstance(v, list):
                    return [x for x in v if isinstance(x, dict)]
        except json.JSONDecodeError:
            return []
        return []

    rows: list[dict[str, Any]] = []
    depth = 0
    in_string = False
    escape = False
    obj_start: int | None = None
    i = start + 1
    while i < len(cleaned):
        ch = cleaned[i]
        if escape:
            escape = False
        elif ch == "\\" and in_string:
            escape = True
        elif ch == '"':
            in_string = not in_string
        elif not in_string:
            if ch == "{":
                if depth == 0:
                    obj_start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and obj_start is not None:
                    chunk = cleaned[obj_start : i + 1]
                    try:
                        rows.append(json.loads(chunk))
                    except json.JSONDecodeError:
                        pass
                    obj_start = None
        i += 1
    return rows


def _validate_rows(raw_rows: list[dict[str, Any]], tier: Tier) -> list[CollegeRow]:
    out: list[CollegeRow] = []
    seen_names: set[str] = set()
    for raw in raw_rows:
        raw["tier"] = tier
        # Coerce probability if model returned percent (0-100).
        prob = raw.get("adjusted_probability")
        if isinstance(prob, (int, float)) and prob > 1.0:
            raw["adjusted_probability"] = prob / 100.0
        try:
            row = CollegeRow.model_validate(raw)
        except ValidationError:
            continue
        if row.name in seen_names:
            continue
        seen_names.add(row.name)
        out.append(row)
    return out


# ────────────────────── core call ──────────────────────


def _generate_one_tier(
    client: Anthropic,
    system_blocks: list[dict[str, Any]],
    profile: StudentProfile,
    scope: Scope,
    tier: Tier,
    target_count: int,
    *,
    raw_dump_path: Path | None = None,
) -> list[CollegeRow]:
    user_message = _tier_user_message(scope, tier, profile, target_count)
    label = f"{_SCOPE_LABELS[scope]} — {tier.upper()}"

    text, _usage = claude_client.call_messages(
        client,
        system_blocks=system_blocks,
        user_message=user_message,
        max_tokens=10000,
        temperature=0.3,
        cache_last_block=True,
        label=label,
    )

    if raw_dump_path is not None:
        raw_dump_path.parent.mkdir(parents=True, exist_ok=True)
        raw_dump_path.write_text(text, encoding="utf-8")

    raw_rows = _salvage_array(text)
    rows = _validate_rows(raw_rows, tier)

    if not rows:
        # Try once more with stricter instruction.
        retry_user = (
            user_message
            + "\n\nCRITICAL: The previous response could not be parsed. "
            "Output ONLY a JSON array, starting with [ and ending with ]. "
            "No prose. No fences. No object wrapper."
        )
        text, _ = claude_client.call_messages(
            client,
            system_blocks=system_blocks,
            user_message=retry_user,
            max_tokens=10000,
            temperature=0.2,
            cache_last_block=True,
            label=f"{label} (재시도)",
        )
        if raw_dump_path is not None:
            raw_dump_path.write_text(text, encoding="utf-8")
        raw_rows = _salvage_array(text)
        rows = _validate_rows(raw_rows, tier)

    logging_ko.info(f"  {tier.upper()}: {len(rows)}개 (목표 {target_count})")
    return rows


def generate_tiered_list(
    profile: StudentProfile,
    scope: Scope,
    grounding_subset: list[CollegeFact],
    client: Anthropic,
    *,
    save_raw_to: Path | None = None,
) -> TieredList:
    """Generate one scope's Reach/Match/Safety tiered list via 3 sub-calls."""

    system_blocks = _build_system_blocks(grounding_subset)
    logging_ko.step(f"=== {_SCOPE_LABELS[scope]} ===")

    # save_raw_to is treated as a directory base; we'll write 3 files inside its parent.
    raw_dir: Path | None = None
    base_name: str | None = None
    if save_raw_to is not None:
        raw_dir = save_raw_to.parent
        base_name = save_raw_to.stem  # e.g. "national"

    def _dump_path(tier: Tier) -> Path | None:
        if raw_dir is None or base_name is None:
            return None
        return raw_dir / f"{base_name}_{tier}.txt"

    reach = _generate_one_tier(
        client, system_blocks, profile, scope, "reach", 50, raw_dump_path=_dump_path("reach")
    )
    match_ = _generate_one_tier(
        client, system_blocks, profile, scope, "match", 50, raw_dump_path=_dump_path("match")
    )
    safety = _generate_one_tier(
        client, system_blocks, profile, scope, "safety", 50, raw_dump_path=_dump_path("safety")
    )

    result = TieredList(scope=scope, reach=reach, match=match_, safety=safety)

    # Also save merged JSON for convenient resume.
    if save_raw_to is not None:
        merged = {
            "scope": scope,
            "reach": [r.model_dump() for r in reach],
            "match": [r.model_dump() for r in match_],
            "safety": [r.model_dump() for r in safety],
        }
        save_raw_to.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    counts = (len(reach), len(match_), len(safety))
    logging_ko.info(
        f"{_SCOPE_LABELS[scope]} 완료: Reach {counts[0]} / Match {counts[1]} / Safety {counts[2]}"
    )
    return result


def generate_all_scopes(
    profile: StudentProfile,
    corpus_curated: dict[Scope, list[CollegeFact]],
    client: Anthropic,
    *,
    raw_response_dir: Path | None = None,
) -> dict[Scope, TieredList]:
    out: dict[Scope, TieredList] = {}
    for scope in ("national_excl_home", "in_state", "lac"):
        save_to = None
        if raw_response_dir is not None:
            fname = {"national_excl_home": "national.json", "in_state": "instate.json", "lac": "lac.json"}[scope]
            save_to = raw_response_dir / fname
        out[scope] = generate_tiered_list(
            profile,
            scope,  # type: ignore[arg-type]
            corpus_curated[scope],  # type: ignore[index]
            client,
            save_raw_to=save_to,
        )
    return out


# Backwards-compatible helper used by generate.py to load a cached merged JSON file.
def _parse_tiered_list(text: str, scope: Scope) -> TieredList:
    cleaned = _strip_fences(text)
    payload = json.loads(cleaned)
    payload["scope"] = scope
    for tier_name in ("reach", "match", "safety"):
        for row in payload.get(tier_name, []) or []:
            row["tier"] = tier_name
    return TieredList.model_validate(payload)
