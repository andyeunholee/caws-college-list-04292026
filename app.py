"""Streamlit web GUI for the CAWS College List generator.

Run locally:
    streamlit run app.py

Deploy to Streamlit Community Cloud (private repo OK):
    1. Push this repo to a private GitHub repo (with .env excluded).
    2. share.streamlit.io → New app → pick repo / branch / app.py.
    3. Settings → Secrets → paste:
           ANTHROPIC_API_KEY = "sk-ant-..."
           ELITE_DATA_DIR = "Elite US College Data Sheet"  # path inside repo
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import traceback
from pathlib import Path
from typing import Callable, Literal

import streamlit as st

# st.set_page_config MUST be the first Streamlit call in the script.
st.set_page_config(
    page_title="CAWS College List Generator",
    page_icon="🎓",
    layout="centered",
)


def _hydrate_env_from_secrets() -> None:
    """On Streamlit Cloud, copy secrets into os.environ before src.config loads.

    Locally there is no secrets.toml — and even probing st.secrets when no
    secrets file exists makes Streamlit display a UI error. So we check for
    a secrets.toml file explicitly first.
    """
    candidate_paths = [
        Path.home() / ".streamlit" / "secrets.toml",
        Path(__file__).resolve().parent / ".streamlit" / "secrets.toml",
    ]
    if not any(p.exists() for p in candidate_paths):
        return
    try:
        for key in ("ANTHROPIC_API_KEY", "ELITE_DATA_DIR"):
            if key in st.secrets and not os.environ.get(key):
                os.environ[key] = str(st.secrets[key])
    except (FileNotFoundError, KeyError):
        pass


_hydrate_env_from_secrets()

from src import config  # noqa: E402
from src.action_plan import generate_action_plan  # noqa: E402
from src.docx_builder import build_docx  # noqa: E402
from src.early_decision import split_ed_ea  # noqa: E402
from src.extractor import extract_profile, save_profile  # noqa: E402
from src.generator import generate_tiered_list  # noqa: E402
from src.grounding import curate_for_scope, load_elite_dataset  # noqa: E402
from src.schema import CollegeRow, Scope, TieredList  # noqa: E402
from src.translator import translate_markdown_to_korean  # noqa: E402
from src.utils import claude_client  # noqa: E402
from src.validator import cross_check  # noqa: E402

LangChoice = Literal["ko", "en", "both"]


def _slugify_ascii(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return text or "Student"


def _select_top_picks(
    scopes: dict[Scope, TieredList], per_scope: int = 8
) -> list[CollegeRow]:
    picks: list[CollegeRow] = []
    for tlist in scopes.values():
        picks.extend(tlist.reach[:per_scope])
        picks.extend(tlist.match[:per_scope])
        picks.extend(tlist.safety[:per_scope])
    return picks


def _run_pipeline(
    raw_text: str,
    lang: LangChoice,
    log: Callable[[str], None],
    *,
    disable_grounding: bool = False,
    research_model: str | None = None,
) -> dict[str, Path]:
    """Drive the full extract → ground → generate → docx pipeline.

    Returns mapping {"ko": path, "en": path} for whichever languages were generated.

    Args:
        disable_grounding: If True, skip the Elite dataset grounding block in
            system prompts and let Claude rely solely on its training knowledge.
        research_model: If set (e.g. "claude-opus-4-7"), used for the per-scope
            tiered list generation calls only. Extraction, action plan and
            translation always use the default Sonnet model for cost reasons.
    """

    config.require_api_key()
    client = claude_client.make_client()

    log("1/7 Extracting profile from student email…")
    profile = extract_profile(raw_text, client)

    today = _dt.date.today().isoformat()
    slug = _slugify_ascii(profile.name)
    out_dir = config.OUTPUT_DIR / f"{slug}_{today}"
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
    top_picks = _select_top_picks(scopes_result)
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

    # Build a normalised set of LAC names from the corpus so Part 3 can tag
    # in-state LACs with "(LAC)". Lookup is case/punctuation-insensitive.
    import re as _re
    lac_names = frozenset(
        _re.sub(r"[^a-z0-9]", "", f.name.lower())
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


# ──────────────────────────────────────────────────────────────────────────────
#                               Streamlit UI
# ──────────────────────────────────────────────────────────────────────────────

st.title("🎓 12th Grade Student College List Generator")
st.caption(
    "Paste a student email → Claude analyzes it and generates a Reach/Match/Safety × National/In-state/LAC × ED/EA list "
    "and an action plan as a Word file."
)

with st.expander("How to use", expanded=False):
    st.markdown(
        """
        1. **Paste the entire body of the email** the student sent into the text box below.
        2. Choose the output language (default: Korean).
        3. Click the **"Generate College List"** button and wait 60–120 seconds.
        4. When finished, you can download the Word file.
        """
    )

raw_text = st.text_area(
    "Student email body",
    height=320,
    placeholder="Paste the full text of the email the student sent here. The more it includes — name, grade, GPA, SAT, activities, intended major, etc. — the more accurate the results.",
    key="raw_email",
)

lang_label = st.radio(
    "Output language",
    options=["Korean", "English", "English + Korean (both)"],
    index=0,
    horizontal=True,
)
lang_map: dict[str, LangChoice] = {
    "Korean": "ko",
    "English": "en",
    "English + Korean (both)": "both",
}
lang: LangChoice = lang_map[lang_label]

with st.expander("Advanced settings (optional)", expanded=False):
    use_grounding = st.checkbox(
        "Use Elite dataset — when on, uses the repo's grounding facts (acceptance rates·ED/EA)",
        value=False,
        help=(
            "Default is OFF (= research with Claude training knowledge only, broader range of recommendations). "
            "When on, the repo's Elite grounding (acceptance rate·ED/EA info for 202 colleges) is "
            "included in the system prompt to improve consistency and accuracy, but "
            "schools outside those 202 are rarely recommended."
        ),
    )
    disable_grounding = not use_grounding
    use_opus_for_research = st.checkbox(
        "Use Opus for the research step (instead of Sonnet)",
        value=False,
        help=(
            "Default is OFF (Sonnet). When on, Opus 4.7 is used only for Reach/Match/Safety list generation "
            "(9 calls total). Reasoning quality↑, cost about 5×↑ (≈ $2-3 per student). "
            "Extraction·action plan·translation always use Sonnet to save cost."
        ),
    )

research_model: str | None = "claude-opus-4-7" if use_opus_for_research else None

generate_clicked = st.button("Generate College List", type="primary", use_container_width=True)

if generate_clicked:
    if not raw_text.strip():
        st.error("Student email body is empty.")
        st.stop()

    status_log: list[str] = []
    status_box = st.status("Running…", expanded=True)

    try:
        with status_box:
            placeholder = st.empty()

            def log(msg: str) -> None:
                status_log.append(msg)
                placeholder.markdown(
                    "```\n" + "\n".join(status_log[-30:]) + "\n```"
                )

            # Patch logging_ko so its messages also stream into the same panel.
            from src.utils import logging_ko as _ko

            _orig = {
                "info": _ko.info,
                "step": _ko.step,
                "warn": _ko.warn,
                "error": _ko.error,
                "cost": _ko.cost,
            }

            def _capture(prefix: str):
                def _fn(msg: str) -> None:
                    log(f"{prefix}{msg}")

                return _fn

            _ko.info = _capture("ℹ ")  # type: ignore[assignment]
            _ko.step = _capture("▶ ")  # type: ignore[assignment]
            _ko.warn = _capture("⚠ ")  # type: ignore[assignment]
            _ko.error = _capture("✖ ")  # type: ignore[assignment]

            def _capture_cost(usage, estimated_usd):  # type: ignore[no-untyped-def]
                in_tok = usage.get("input_tokens", 0)
                cw = usage.get("cache_creation_input_tokens", 0)
                cr = usage.get("cache_read_input_tokens", 0)
                out_tok = usage.get("output_tokens", 0)
                log(
                    f"$ input {in_tok:,} / cacheW {cw:,} / cacheR {cr:,} / "
                    f"output {out_tok:,} → approx. ${estimated_usd:.4f}"
                )

            _ko.cost = _capture_cost  # type: ignore[assignment]
            try:
                written = _run_pipeline(
                    raw_text,
                    lang,
                    log,
                    disable_grounding=disable_grounding,
                    research_model=research_model,
                )
            finally:
                for k, v in _orig.items():
                    setattr(_ko, k, v)

            placeholder.markdown("```\n" + "\n".join(status_log) + "\n```")
        status_box.update(label="Done ✅", state="complete", expanded=False)
    except Exception as e:  # noqa: BLE001 — surface any pipeline error to the UI
        status_box.update(label="Failed ❌", state="error", expanded=True)
        st.error(f"Error: {e}")
        st.code(traceback.format_exc(), language="text")
        st.stop()

    # Persist generated file paths across reruns so download buttons don't
    # disappear after the user clicks one. (Streamlit reruns the whole script
    # on every widget interaction; `generate_clicked` flips back to False, so
    # without session_state the second download button would vanish.)
    st.session_state["generated_files"] = {k: str(v) for k, v in written.items()}

generated = st.session_state.get("generated_files")
if generated:
    st.success(f"{len(generated)} Word file(s) generated.")
    st.caption(
        f"Files are also permanently saved in the `output/` folder: "
        f"`{Path(next(iter(generated.values()))).parent}`"
    )
    for lang_code, path_str in generated.items():
        path = Path(path_str)
        if not path.exists():
            st.warning(f"File not found: {path.name}")
            continue
        label = "Korean (.docx)" if lang_code == "ko" else "English (.docx)"
        st.download_button(
            label=f"⬇ Download {label} — {path.name}",
            data=path.read_bytes(),
            file_name=path.name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            key=f"download_{lang_code}",
        )
