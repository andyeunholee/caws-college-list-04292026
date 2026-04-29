"""CLI entry point: pasted student email → personalized college-list .docx."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

from src import config
from src.action_plan import generate_action_plan
from src.docx_builder import build_docx
from src.early_decision import split_ed_ea
from src.extractor import extract_profile, load_profile, save_profile
from src.generator import generate_all_scopes
from src.grounding import EliteCorpus, curate_for_scope, load_elite_dataset
from src.schema import CollegeRow, Scope, StudentProfile, TieredList
from src.translator import translate_markdown_to_korean
from src.utils import claude_client, logging_ko
from src.validator import cross_check


def _slugify_ascii(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return text or "Student"


def _read_stdin_paste() -> str:
    print(
        "\n학생 이메일 본문을 아래에 붙여넣으세요.\n"
        "끝낼 때는 빈 줄에서 'EOF'를 입력하거나 Ctrl+Z(Windows) / Ctrl+D(Mac)를 누르세요.\n"
        "─" * 60
    )
    lines: list[str] = []
    try:
        for line in sys.stdin:
            if line.strip() == "EOF":
                break
            lines.append(line)
    except KeyboardInterrupt:
        print()
    text = "".join(lines).strip()
    if not text:
        raise SystemExit("입력된 텍스트가 없습니다.")
    return text


def _student_dir(profile: StudentProfile) -> Path:
    today = _dt.date.today().isoformat()
    slug = _slugify_ascii(profile.name)
    return config.OUTPUT_DIR / f"{slug}_{today}"


def _print_dry_run(
    profile: StudentProfile,
    scopes: dict[Scope, TieredList],
    ed_rows: list[CollegeRow],
    ea_rows: list[CollegeRow],
    action_plan_md: str,
) -> None:
    print("\n" + "=" * 60)
    print(f"DRY RUN PREVIEW — {profile.name}")
    print("=" * 60)
    for scope, tlist in scopes.items():
        print(f"\n## {scope}")
        for tier in ("reach", "match", "safety"):
            rows = getattr(tlist, tier)
            print(f"\n### {tier.upper()} ({len(rows)})")
            for r in rows[:10]:
                print(f"  - {r.name} ({r.state}) — {r.adjusted_probability * 100:.0f}% — {r.reasoning_factor}")
            if len(rows) > 10:
                print(f"  … {len(rows) - 10} more")
    print(f"\n## ED-eligible: {len(ed_rows)}")
    print(f"## EA/REA/SCEA-eligible: {len(ea_rows)}")
    print("\n## Action Plan\n")
    print(action_plan_md)


def _select_top_picks(scopes: dict[Scope, TieredList], per_scope: int = 8) -> list[CollegeRow]:
    """For the action-plan call: top reaches, top matches, top safeties from each scope."""
    picks: list[CollegeRow] = []
    for tlist in scopes.values():
        picks.extend(tlist.reach[:per_scope])
        picks.extend(tlist.match[:per_scope])
        picks.extend(tlist.safety[:per_scope])
    return picks


def _ensure_state(profile: StudentProfile) -> None:
    if not profile.state:
        logging_ko.warn(
            "학생의 거주 주(state)가 비어있습니다. In-state 리스트는 생성할 수 없으며, "
            "전국 리스트의 홈스테이트 제외도 적용되지 않습니다."
        )


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="12학년 학생 College List 생성기 (CAWS) — paste an email, get a .docx"
    )
    parser.add_argument("--input", type=Path, help="학생 이메일이 들어있는 텍스트 파일 경로")
    parser.add_argument("--dry-run", action="store_true", help=".docx 생성 없이 markdown 미리보기만")
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="기존 student_profile.json을 재사용 (학생 이름 또는 폴더명)",
    )
    parser.add_argument(
        "--scope",
        choices=["national", "instate", "lac", "ed_ea", "action", "all"],
        default="all",
        help="특정 섹션만 재생성",
    )
    parser.add_argument(
        "--lang",
        choices=["both", "en", "ko"],
        default="both",
        help="출력 언어. both=영문+한글 두 파일 (기본), en=영문만, ko=한글만",
    )
    args = parser.parse_args(argv)

    config.require_api_key()  # raises if missing
    client = claude_client.make_client()

    # ── Step 1: profile ────────────────────────────────────────────────────
    profile: StudentProfile
    if args.resume:
        candidate = config.OUTPUT_DIR / args.resume
        if candidate.is_dir():
            profile_path = candidate / "student_profile.json"
        else:
            slug = _slugify_ascii(args.resume)
            today = _dt.date.today().isoformat()
            profile_path = config.OUTPUT_DIR / f"{slug}_{today}" / "student_profile.json"
        if not profile_path.exists():
            raise SystemExit(f"--resume 대상 student_profile.json을 찾을 수 없습니다: {profile_path}")
        logging_ko.info(f"기존 프로필 재사용: {profile_path}")
        profile = load_profile(profile_path)
    else:
        if args.input:
            raw_text = args.input.read_text(encoding="utf-8")
            logging_ko.info(f"학생 이메일을 파일에서 읽음: {args.input}")
        else:
            raw_text = _read_stdin_paste()
        profile = extract_profile(raw_text, client)

    _ensure_state(profile)

    out_dir = _student_dir(profile)
    raw_dir = out_dir / "raw_responses"
    out_dir.mkdir(parents=True, exist_ok=True)
    save_profile(profile, out_dir / "student_profile.json")

    # ── Step 2: grounding ──────────────────────────────────────────────────
    corpus: EliteCorpus = load_elite_dataset(config.ELITE_DATA_DIR)

    curated: dict[Scope, list] = {
        "national_excl_home": curate_for_scope(corpus, "national_excl_home", profile.state),
        "in_state": curate_for_scope(corpus, "in_state", profile.state),
        "lac": curate_for_scope(corpus, "lac", profile.state),
    }

    logging_ko.info(
        f"Grounding 큐레이션: National {len(curated['national_excl_home'])}, "
        f"In-state {len(curated['in_state'])}, LAC {len(curated['lac'])}"
    )

    # ── Step 3: generate per scope ─────────────────────────────────────────
    scopes_to_run: list[Scope]
    if args.scope == "national":
        scopes_to_run = ["national_excl_home"]
    elif args.scope == "instate":
        scopes_to_run = ["in_state"]
    elif args.scope == "lac":
        scopes_to_run = ["lac"]
    else:
        scopes_to_run = ["national_excl_home", "in_state", "lac"]

    scope_filenames = {
        "national_excl_home": "national.json",
        "in_state": "instate.json",
        "lac": "lac.json",
    }

    scopes_result: dict[Scope, TieredList] = {}
    for scope in scopes_to_run:
        from src.generator import generate_tiered_list, _parse_tiered_list  # type: ignore
        cached_path = raw_dir / scope_filenames[scope]
        if args.resume and cached_path.exists():
            logging_ko.info(f"[resume] 캐시된 {scope} 결과 재사용: {cached_path.name}")
            scopes_result[scope] = _parse_tiered_list(cached_path.read_text(encoding="utf-8"), scope)  # type: ignore[arg-type]
            continue
        scopes_result[scope] = generate_tiered_list(
            profile,
            scope,
            curated[scope],
            client,
            save_raw_to=cached_path,
        )

    # Fill remaining scopes (when --scope was a partial selection) from disk if cached.
    for scope in ("national_excl_home", "in_state", "lac"):
        if scope not in scopes_result:
            from src.generator import _parse_tiered_list  # type: ignore
            cached_path = raw_dir / scope_filenames[scope]
            if cached_path.exists():
                scopes_result[scope] = _parse_tiered_list(cached_path.read_text(encoding="utf-8"), scope)  # type: ignore[arg-type]
            else:
                scopes_result[scope] = TieredList(scope=scope)  # type: ignore[arg-type]

    # ── Step 4: validate ──────────────────────────────────────────────────
    all_rows = (
        scopes_result["national_excl_home"].all_rows()
        + scopes_result["in_state"].all_rows()
        + scopes_result["lac"].all_rows()
    )
    flags = cross_check(all_rows, corpus)
    if flags:
        warn_count = sum(1 for f in flags if f.severity == "warning")
        logging_ko.info(
            f"내부 검증: {len(flags)}건 (warning {warn_count}) — "
            "주로 Top 100 데이터셋 외 학교라 발생. 학생용 문서에는 표시되지 않음."
        )

    # ── Step 5: ED / EA split ─────────────────────────────────────────────
    ed_rows, ea_rows = split_ed_ea(all_rows, corpus)
    logging_ko.info(f"ED 가능 {len(ed_rows)}개 / EA·REA·SCEA 가능 {len(ea_rows)}개")

    # ── Step 6: action plan ───────────────────────────────────────────────
    action_plan_path = raw_dir / "action_plan.md"
    if args.resume and action_plan_path.exists() and args.scope in ("all",):
        logging_ko.info(f"[resume] 캐시된 액션 플랜 재사용: {action_plan_path.name}")
        action_plan_md = action_plan_path.read_text(encoding="utf-8")
    elif args.scope in ("all", "action"):
        top_picks = _select_top_picks(scopes_result)
        action_plan_md = generate_action_plan(
            profile, top_picks, client, save_raw_to=action_plan_path
        )
    else:
        action_plan_md = action_plan_path.read_text(encoding="utf-8") if action_plan_path.exists() else ""

    # ── Step 7: dry run or docx ───────────────────────────────────────────
    if args.dry_run:
        _print_dry_run(profile, scopes_result, ed_rows, ea_rows, action_plan_md)
        return 0

    # ── Step 7a: Korean translation of action plan (only if KO output requested) ──
    action_plan_md_ko: str = ""
    if args.lang in ("both", "ko") and action_plan_md:
        ko_path = raw_dir / "action_plan_ko.md"
        action_plan_md_ko = translate_markdown_to_korean(
            action_plan_md, client, save_to=ko_path, label="액션 플랜 한글 번역"
        )

    today = _dt.date.today().isoformat()
    slug = _slugify_ascii(profile.name)

    targets: list[tuple[str, str, str]] = []  # (lang, suffix, action_plan_md)
    if args.lang in ("both", "en"):
        targets.append(("en", "", action_plan_md))
    if args.lang in ("both", "ko"):
        targets.append(("ko", "_KR", action_plan_md_ko or action_plan_md))

    written_paths: list[Path] = []
    for lang, file_suffix, plan_md in targets:
        base_path = out_dir / f"{slug}_college_list_{today}{file_suffix}.docx"
        docx_path = base_path
        suffix = 2
        while True:
            try:
                build_docx(
                    profile=profile,
                    national=scopes_result["national_excl_home"],
                    instate=scopes_result["in_state"],
                    lac=scopes_result["lac"],
                    ed_rows=ed_rows,
                    ea_rows=ea_rows,
                    action_plan_md=plan_md or "_(액션 플랜이 이번 실행에서 생성되지 않았습니다.)_",
                    flags=flags,
                    out_path=docx_path,
                    lang=lang,  # type: ignore[arg-type]
                )
                break
            except PermissionError:
                logging_ko.warn(
                    f"파일이 잠겨 있습니다(아마 Word에서 열려 있음): {docx_path.name} → 다른 이름으로 저장합니다."
                )
                docx_path = base_path.with_name(
                    f"{base_path.stem}_v{suffix}{base_path.suffix}"
                )
                suffix += 1
                if suffix > 9:
                    raise
        written_paths.append(docx_path)
        logging_ko.step(f"완료 ({lang.upper()}): {docx_path}")

    if len(written_paths) > 1:
        logging_ko.info(f"총 {len(written_paths)}개 Word 파일 생성됨.")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
