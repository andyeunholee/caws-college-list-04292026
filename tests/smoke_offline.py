"""Offline smoke test: exercises everything except live Claude calls.

Run from project root:
    python tests/smoke_offline.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import config
from src.docx_builder import build_docx
from src.early_decision import split_ed_ea
from src.grounding import curate_for_scope, load_elite_dataset
from src.schema import (
    Award,
    CollegeRow,
    CourseworkItem,
    StudentProfile,
    TieredList,
)
from src.utils import logging_ko
from src.validator import cross_check


def _fake_profile() -> StudentProfile:
    return StudentProfile(
        name="Yena Seo",
        grade="12",
        high_school="North Gwinnett High School",
        state="GA",
        city="Suwanee",
        gpa_unweighted=3.96,
        gpa_weighted=4.52,
        class_rank="14/612",
        sat_total=1480,
        sat_ebrw=700,
        sat_math=780,
        act_composite=33,
        intended_major="Biology",
        career_goal="Pre-Med",
        coursework=[
            CourseworkItem(name="AP Biology", type="AP", grade="5"),
            CourseworkItem(name="AP Calculus BC", type="AP"),
            CourseworkItem(name="Anatomy & Physiology I (DE)", type="DE"),
        ],
        awards=[
            Award(name="National Merit Semifinalist", level="National", year="2024"),
            Award(name="HOSA State Champion", level="State", year="2024"),
        ],
        community_service_hours=270,
        narrative_notes="Strong HOSA + clinical hours; SAT EBRW the relative weakness.",
    )


def _fake_row(name: str, state: str, tier: str, prob: float, *, ed=None, ea=None, rea=None) -> CollegeRow:
    return CollegeRow(
        name=name,
        state=state,
        tier=tier,
        adjusted_probability=prob,
        reasoning_factor="synthetic test row",
        has_ed=ed,
        has_ea=ea,
        has_rea_or_scea=rea,
    )


def _fake_tiered(scope: str) -> TieredList:
    return TieredList(
        scope=scope,
        reach=[
            _fake_row("Duke University", "NC", "reach", 0.10, ed=True),
            _fake_row("Cornell University", "NY", "reach", 0.12, ed=True),
            _fake_row("Princeton University", "NJ", "reach", 0.05, rea=True),
        ],
        match=[
            _fake_row("Boston University", "MA", "match", 0.32, ed=True),
            _fake_row("University of Wisconsin-Madison", "WI", "match", 0.45, ea=True),
            _fake_row("Hypothetical Made-Up College", "CA", "match", 0.40),
        ],
        safety=[
            _fake_row("University of Alabama", "AL", "safety", 0.85, ea=True),
            _fake_row("Ohio State University", "OH", "safety", 0.70, ea=True),
        ],
    )


def main() -> int:
    logging_ko.step("1) Elite 데이터셋 로드 중…")
    corpus = load_elite_dataset(config.ELITE_DATA_DIR)
    assert len(corpus.all()) > 100, "기대보다 적은 대학 수: %d" % len(corpus.all())

    logging_ko.step("2) Scope 큐레이션 (GA 학생) 검증…")
    nat = curate_for_scope(corpus, "national_excl_home", "GA")
    in_state = curate_for_scope(corpus, "in_state", "GA")
    lac = curate_for_scope(corpus, "lac", "GA")
    logging_ko.info(f"national {len(nat)} / in-state {len(in_state)} / lac {len(lac)}")
    assert all(f.state != "GA" for f in nat), "national 리스트에 GA가 섞여 있음"
    assert all(not f.is_lac for f in nat), "national 리스트에 LAC가 섞여 있음"
    assert all(f.state == "GA" for f in in_state), "in-state가 GA 외 주 포함"
    assert all(f.is_lac for f in lac), "lac에 LAC 아닌 학교 포함"
    assert len(in_state) >= 2, "GA 4년제 대학이 너무 적음"

    profile = _fake_profile()
    national = _fake_tiered("national_excl_home")
    instate = _fake_tiered("in_state")
    lac_t = _fake_tiered("lac")
    all_rows = national.all_rows() + instate.all_rows() + lac_t.all_rows()

    logging_ko.step("3) Validator: 가짜 대학에 경고가 떠야 함…")
    flags = cross_check(all_rows, corpus)
    fake_flag = next(
        (f for f in flags if f.college_name == "Hypothetical Made-Up College"),
        None,
    )
    assert fake_flag is not None, "Validator가 가짜 대학을 잡지 못함"
    logging_ko.info(f"검증 경고 {len(flags)}건 (예상대로 'Hypothetical Made-Up College' 포함)")

    logging_ko.step("4) ED/EA split…")
    ed_rows, ea_rows = split_ed_ea(all_rows, corpus)
    assert any(r.name == "Duke University" for r in ed_rows), "Duke가 ED 리스트에 없음"
    assert any(r.name == "Princeton University" for r in ea_rows), "Princeton(REA)이 EA 리스트에 없음"
    assert not any(r.name == "Duke University" for r in ea_rows), "Duke가 EA에 잘못 들어감"
    logging_ko.info(f"ED {len(ed_rows)}개 / EA·REA·SCEA {len(ea_rows)}개")

    logging_ko.step("5) docx 어셈블리…")
    out_path = ROOT / "output" / "_smoke_test" / "smoke_test.docx"
    build_docx(
        profile=profile,
        national=national * 1 if False else national,  # noqa
        instate=instate,
        lac=lac_t,
        ed_rows=ed_rows,
        ea_rows=ea_rows,
        action_plan_md=(
            "## Strategy Snapshot\n\n"
            "Solid Pre-Med profile; **EBRW 700** is the clearest near-term lever.\n\n"
            "## Highest-Leverage Actions (Top 5, Ranked)\n\n"
            "1. **Retake SAT in August** — target EBRW ≥ 730 to clear 1500.\n"
            "2. **Lock in QuestBridge ranking** — finalize partner-school rank order.\n"
            "3. **Secure HPAC track** — request committee letter pre-screen by July.\n"
            "4. **Write the clinical-narrative essay** — tie pediatric ward hours to Pre-Med thesis.\n"
            "5. **Visit Emory & Duke** — demonstrated interest in two top picks.\n"
        ),
        flags=flags,
        out_path=out_path,
    )
    assert out_path.exists() and out_path.stat().st_size > 5000, "docx 파일이 만들어지지 않거나 너무 작음"
    logging_ko.step(f"docx 생성 성공: {out_path} ({out_path.stat().st_size:,} bytes)")

    logging_ko.step("모든 오프라인 스모크 테스트 통과 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
