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
    page_title="CAWS College List 생성기",
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
) -> dict[str, Path]:
    """Drive the full extract → ground → generate → docx pipeline.

    Returns mapping {"ko": path, "en": path} for whichever languages were generated.
    """

    config.require_api_key()
    client = claude_client.make_client()

    log("1/7 학생 이메일에서 프로필 추출 중…")
    profile = extract_profile(raw_text, client)

    today = _dt.date.today().isoformat()
    slug = _slugify_ascii(profile.name)
    out_dir = config.OUTPUT_DIR / f"{slug}_{today}"
    raw_dir = out_dir / "raw_responses"
    out_dir.mkdir(parents=True, exist_ok=True)
    save_profile(profile, out_dir / "student_profile.json")
    log(f"   → 학생 이름: {profile.name} / 주: {profile.state or '미상'}")

    log("2/7 Elite 데이터셋 로딩 및 큐레이션 중…")
    corpus = load_elite_dataset(config.ELITE_DATA_DIR)
    curated = {
        "national_excl_home": curate_for_scope(corpus, "national_excl_home", profile.state),
        "in_state": curate_for_scope(corpus, "in_state", profile.state),
        "lac": curate_for_scope(corpus, "lac", profile.state),
    }
    log(
        f"   → National {len(curated['national_excl_home'])} / "
        f"In-state {len(curated['in_state'])} / LAC {len(curated['lac'])}"
    )

    scope_filenames = {
        "national_excl_home": "national.json",
        "in_state": "instate.json",
        "lac": "lac.json",
    }
    scopes_result: dict[Scope, TieredList] = {}
    for i, scope in enumerate(("national_excl_home", "in_state", "lac"), start=3):
        log(f"{i}/7 Claude로 {scope} 리스트 생성 중… (60-90초)")
        cached_path = raw_dir / scope_filenames[scope]
        scopes_result[scope] = generate_tiered_list(
            profile, scope, curated[scope], client, save_raw_to=cached_path
        )
        log(
            f"   → reach {len(scopes_result[scope].reach)} / "
            f"match {len(scopes_result[scope].match)} / "
            f"safety {len(scopes_result[scope].safety)}"
        )

    log("6/7 ED/EA 분류 + 검증 중…")
    all_rows = (
        scopes_result["national_excl_home"].all_rows()
        + scopes_result["in_state"].all_rows()
        + scopes_result["lac"].all_rows()
    )
    flags = cross_check(all_rows, corpus)
    ed_rows, ea_rows = split_ed_ea(all_rows, corpus)
    log(f"   → ED 가능 {len(ed_rows)} / EA·REA·SCEA 가능 {len(ea_rows)}")

    log("7/7 액션 플랜 + Word 파일 생성 중…")
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
            label="액션 플랜 한글 번역",
        )

    targets: list[tuple[str, str, str]] = []
    if lang in ("both", "en"):
        targets.append(("en", "", action_plan_md))
    if lang in ("both", "ko"):
        targets.append(("ko", "_KR", action_plan_md_ko or action_plan_md))

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
                    or "_(액션 플랜이 이번 실행에서 생성되지 않았습니다.)_",
                    flags=flags,
                    out_path=docx_path,
                    lang=lang_code,  # type: ignore[arg-type]
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

    log("완료.")
    return written


# ──────────────────────────────────────────────────────────────────────────────
#                               Streamlit UI
# ──────────────────────────────────────────────────────────────────────────────

st.title("🎓 12학년 학생 College List 생성기")
st.caption(
    "학생 이메일을 paste → Claude가 분석해서 Reach/Match/Safety × National/In-state/LAC × ED/EA 리스트와 "
    "액션 플랜을 Word 파일로 생성합니다."
)

with st.expander("사용법", expanded=False):
    st.markdown(
        """
        1. 아래 텍스트 박스에 학생이 보낸 **이메일 본문 전체를 paste**하세요.
        2. 출력 언어를 고르세요 (기본: 한글).
        3. **"College List 생성"** 버튼을 누르고 60–120초 기다리세요.
        4. 완료되면 Word 파일을 다운로드할 수 있습니다.
        """
    )

raw_text = st.text_area(
    "학생 이메일 본문",
    height=320,
    placeholder="여기에 학생이 보낸 이메일 텍스트 전체를 붙여넣으세요. 이름, 학년, GPA, SAT, 활동, 관심 전공 등이 포함되어 있을수록 정확도가 올라갑니다.",
    key="raw_email",
)

lang_label = st.radio(
    "출력 언어",
    options=["한글", "영문", "영문 + 한글 (둘 다)"],
    index=0,
    horizontal=True,
)
lang_map: dict[str, LangChoice] = {
    "한글": "ko",
    "영문": "en",
    "영문 + 한글 (둘 다)": "both",
}
lang: LangChoice = lang_map[lang_label]

generate_clicked = st.button("College List 생성", type="primary", use_container_width=True)

if generate_clicked:
    if not raw_text.strip():
        st.error("학생 이메일 본문이 비어 있습니다.")
        st.stop()

    status_log: list[str] = []
    status_box = st.status("실행 중…", expanded=True)

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
                    f"$ 입력 {in_tok:,} / 캐시W {cw:,} / 캐시R {cr:,} / "
                    f"출력 {out_tok:,} → 약 ${estimated_usd:.4f}"
                )

            _ko.cost = _capture_cost  # type: ignore[assignment]
            try:
                written = _run_pipeline(raw_text, lang, log)
            finally:
                for k, v in _orig.items():
                    setattr(_ko, k, v)

            placeholder.markdown("```\n" + "\n".join(status_log) + "\n```")
        status_box.update(label="완료 ✅", state="complete", expanded=False)
    except Exception as e:  # noqa: BLE001 — surface any pipeline error to the UI
        status_box.update(label="실패 ❌", state="error", expanded=True)
        st.error(f"오류: {e}")
        st.code(traceback.format_exc(), language="text")
        st.stop()

    st.success(f"{len(written)}개 Word 파일이 생성되었습니다.")
    for lang_code, path in written.items():
        label = "한글 (.docx)" if lang_code == "ko" else "영문 (.docx)"
        st.download_button(
            label=f"⬇ {label} 다운로드 — {path.name}",
            data=path.read_bytes(),
            file_name=path.name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
