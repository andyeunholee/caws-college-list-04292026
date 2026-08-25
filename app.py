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

import os
import traceback
from pathlib import Path

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

from src.pipeline import LangChoice, run_pipeline  # noqa: E402


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
                written = run_pipeline(
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
