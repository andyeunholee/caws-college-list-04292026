"""Shared end-to-end pipeline: raw email/survey text → EN/KR .docx files.

Used by both the Streamlit GUI (app.py) and the headless survey worker
(automation/survey_worker.py) so the two never drift apart.
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Callable, Literal

from . import config
from .action_plan import generate_action_plan
from .docx_builder import build_docx
from .early_decision import split_ed_ea
from .extractor import extract_profile, save_profile
from .generator import generate_tiered_list
from .grounding import curate_for_scope, load_elite_dataset
from .schema import CollegeRow, Scope, TieredList
from .translator import translate_markdown_to_korean
from .utils import claude_client
from .validator import cross_check

LangChoice = Literal["ko", "en", "both"]


def slugify_ascii(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return text or "Student"


def select_top_picks(
    scopes: dict[Scope, TieredList], per_scope: int = 8
) -> list[CollegeRow]:
    picks: list[CollegeRow] = []
    for tlist in scopes.values():
        picks.extend(tlist.reach[:per_scope])
        picks.extend(tlist.match[:per_scope])
        picks.extend(tlist.safety[:per_scope])
    return picks


def run_pipeline(
    raw_text: str,
    lang: LangChoice,
    log: Callable[[str], None],
    *,
    disable_grounding: bool = False,
    research_model: str | None = None,
    output_root: Path | None = None,
) -> dict[str, Path]:
    """Drive the full extract → ground → generate → docx pipeline.

    Returns mapping {"ko": path, "en": path} for whichever languages were generated.

    Args:
        disable_grounding: If True, skip the Elite dataset grounding block in
            system prompts and let Claude rely solely on its training knowledge.
        research_model: If set (e.g. "claude-opus-4-7"), used for the per-scope
            tiered list generation calls only. Extraction, action plan and
            translation always use the default Sonnet model for cost reasons.
        output_root: Folder under which the per-student output directory is
            created. Defaults to config.OUTPUT_DIR.
    """

    config.require_api_key()
    client = claude_client.make_client()

    log("1/7 Extracting profile from student email…")
    profile = extract_profile(raw_text, client)

    today = _dt.date.today().isoformat()
    slug = slugify_ascii(profile.name)
    out_dir = (output_root or config.OUTPUT_DIR) / f"{slug}_{today}"
    raw_dir = out_dir / "raw_responses"
    out_dir.mkdir(parents=True, exist_ok=True)
    save_profile(profile, out_dir / "student_profile.json")
    log(f"   → Student name: {profile.name} / State: {profile.state or 'Unknown'}")

    log("2/7 Loading and curating Elite dataset…")
    corpus = load_elite_dataset(config.ELITE_DATA_DIR)
    if disable_grounding:
        log("   ⓘ Grounding OFF — using Claude training knowledge only")
    curated = {
        "national_excl_home": curate_for_scope(corpus, "national_excl_home", profile.state),
        "in_state": curate_for_scope(corpus, "in_state", profile.state),
        "lac": curate_for_scope(corpus, "lac", profile.state),
    }
    log(
        f"   → National {len(curated['national_excl_home'])} / "
        f"In-state {len(curated['in_state'])} / LAC {len(curated['lac'])}"
    )

    if research_model:
        log(f"   ⓘ Research model: {research_model} (applied to generation step only)")

    scope_filenames = {
        "national_excl_home": "national.json",
        "in_state": "instate.json",
        "lac": "lac.json",
    }
    scopes_result: dict[Scope, TieredList] = {}
    for i, scope in enumerate(("national_excl_home", "in_state", "lac"), start=3):
        log(f"{i}/7 Generating {scope} list with Claude… (60-90 sec)")
        cached_path = raw_dir / scope_filenames[scope]
        scopes_result[scope] = generate_tiered_list(
            profile, scope, curated[scope], client,
            save_raw_to=cached_path,
            disable_grounding=disable_grounding,
            model_override=research_model,
        )
        log(
            f"   → reach {len(scopes_result[scope].reach)} / "
            f"match {len(scopes_result[scope].match)} / "
            f"safety {len(scopes_result[scope].safety)}"
        )

    log("6/7 Classifying ED/EA + validating…")
    all_rows = (
        scopes_result["national_excl_home"].all_rows()
        + scopes_result["in_state"].all_rows()
        + scopes_result["lac"].all_rows()
    )
    flags = cross_check(all_rows, corpus)
    ed_rows, ea_rows = split_ed_ea(all_rows, corpus)
    log(f"   → ED eligible {len(ed_rows)} / EA·REA·SCEA eligible {len(ea_rows)}")

    log("7/7 Generating action plan + Word file…")
    top_picks = select_top_picks(scopes_result)
    action_plan_md = generate_action_plan(
        profile, top_picks, client, save_raw_to=raw_dir / "action_plan.md"
    )

    action_plan_md_ko = ""
    if lang in ("both", "ko") and action_plan_md:
        action_plan_md_ko = translate_markdown_to_korean(
            action_plan_md,
            client,
            save_to=raw_dir / "action_plan_ko.md",
            label="Action plan Korean translation",
        )

    targets: list[tuple[str, str, str]] = []
    if lang in ("both", "en"):
        targets.append(("en", "", action_plan_md))
    if lang in ("both", "ko"):
        targets.append(("ko", "_KR", action_plan_md_ko or action_plan_md))

    # Normalised set of LAC names from the corpus so the in-state section can
    # tag LACs with "(LAC)". Lookup is case/punctuation-insensitive.
    lac_names = frozenset(
        re.sub(r"[^a-z0-9]", "", f.name.lower())
        for f in corpus.all()
        if f.is_lac
    )

    written: dict[str, Path] = {}
    for lang_code, file_suffix, plan_md in targets:
        base_path = out_dir / f"{slug}_college_list_{today}{file_suffix}.docx"
        docx_path = base_path
        attempt = 2
        while True:
            try:
                build_docx(
                    profile=profile,
                    national=scopes_result["national_excl_home"],
                    instate=scopes_result["in_state"],
                    lac=scopes_result["lac"],
                    ed_rows=ed_rows,
                    ea_rows=ea_rows,
                    action_plan_md=plan_md
                    or "_(No action plan was generated in this run.)_",
                    flags=flags,
                    out_path=docx_path,
                    lang=lang_code,  # type: ignore[arg-type]
                    lac_names=lac_names,
                )
                break
            except PermissionError:
                docx_path = base_path.with_name(
                    f"{base_path.stem}_v{attempt}{base_path.suffix}"
                )
                attempt += 1
                if attempt > 9:
                    raise
        written[lang_code] = docx_path
        log(f"   ✓ ({lang_code.upper()}) {docx_path.name}")

    log("Done.")
    return written
