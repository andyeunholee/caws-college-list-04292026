"""Static UI string mappings for English and Korean Word output.

Dynamic content (action plan markdown, narrative notes) is translated by
src.translator via the Claude API. Everything else lives here for accuracy
and zero translation cost.
"""

from __future__ import annotations

from typing import Literal

Lang = Literal["en", "ko"]


STRINGS: dict[Lang, dict[str, str]] = {
    "en": {
        # ─── Page header / footer ───
        "page_header_template": "{name} — College List Strategy Report",
        "page_footer_page_prefix": "Page ",
        "page_footer_of": " of ",

        # ─── Title block ───
        "report_title": "College List Strategy Report",
        "subtitle_qb_track": "Prepared for QuestBridge-track candidates",
        "subtitle_default": "Personalized Reach / Match / Safety tiered list",

        # ─── Profile snapshot ───
        "profile_h1": "Student Profile Snapshot",
        "profile_metric_header": "Metric",
        "profile_value_header": "Value",
        "profile_label_high_school": "High School",
        "profile_label_intended_track": "Intended Track",
        "profile_label_uw_gpa": "UW GPA",
        "profile_label_w_gpa": "W GPA",
        "profile_label_class_rank": "Class Rank",
        "profile_label_sat": "SAT",
        "profile_label_sat_value": "{total} (EBRW {ebrw} / Math {math})",
        "profile_label_act": "ACT",
        "profile_label_ap_ib_de": "AP / IB / DE",
        "profile_label_awards": "Awards",
        "profile_label_service": "Service",
        "profile_label_leadership": "Leadership",
        "profile_label_program": "Program",
        "profile_value_questbridge_planned": "QuestBridge planned",
        "profile_courses_unit": "{n} courses",
        "profile_hours_unit": "{n}+ hours",
        "profile_positions_unit": "{n} positions",
        "profile_value_dash": "—",

        # ─── Probability note ───
        "note_h1": "A Note on How the Probabilities Were Derived",
        "note_intro": (
            "The percentages next to each school are not the school's published "
            "overall acceptance rate. They are profile-adjusted estimated "
            "probabilities that combine:"
        ),
        "note_bullet_cds": (
            "The school's most recently published Common Data Set (CDS) / "
            "admissions data"
        ),
        "note_bullet_sat_gap": (
            "The gap between {name}'s {sat_token} and the school's middle 50% SAT band"
        ),
        "note_bullet_gpa_rank": "{name}'s GPA and class rank relative to admitted students",
        "note_bullet_premed": (
            "Pre-Med (or intended-major) applicant pool competitiveness, "
            "often more saturated than the general pool"
        ),
        "note_bullet_qb": (
            "QuestBridge Finalist boost (for QB partner schools, if she becomes a "
            "Finalist, effective probability rises 2-4x)"
        ),
        "note_bullet_hooks": (
            "Hooks: legacy, recruited athlete, demonstrated interest where colleges "
            "track it"
        ),
        "note_bullet_sffa": (
            "Post-SFFA landscape (race-conscious admissions are no longer permitted; "
            "effect on Asian American applicants is modestly positive at highly "
            "selective schools)"
        ),
        "note_bullet_oos": "Asian / OOS bucket demand pressure at elite public flagships",
        "note_band_line": "Reach = below ~20%   ·   Match = ~20-55%   ·   Safety = ~60%+",
        "note_warn_sat": (
            "⚠ The SAT {sat} is the single biggest drag on the top-tier list. "
            "If {name} can retake in August/September and push to 1480+ "
            "(especially on EBRW), most 'Reach' lines shift up by roughly one tier. "
            "Lists assume the current {sat}."
        ),
        "sat_token_with_value": "{val} SAT",
        "sat_token_default": "current SAT",

        # ─── Parts ───
        "part1_h1": (
            "Part 1 — National Universities List "
            "(All colleges in the home state — including LACs — are excluded)"
        ),
        "part2_h1": "Part 2 — Liberal Arts Colleges Nationwide (Excluding home-state LACs)",
        "part2_intro": (
            "LACs are a strategically important segment for Pre-Med because of "
            "strong advising, small class sizes, and — critically — deep QuestBridge "
            "partnership density. LACs located in the student's home state are "
            "intentionally listed in Part 3 instead of here. ⭐ QB marks colleges that "
            "are QuestBridge National College Match partners."
        ),
        "part3_h1": "Part 3 — {state} Home-State Colleges (LACs included)",
        "part3_intro": (
            "All colleges in {state} are listed here — both LACs and non-LACs. "
            "LACs are tagged with \"(LAC)\" next to the school name. "
            "In-state tuition and state-merit scholarship eligibility are the "
            "strongest practical drivers in this section."
        ),
        "part4_h1": "Part 4 — Early Decision (ED) Options",
        "part4_intro": (
            "ED is binding. If matched, the student must attend. ED round acceptance "
            "rates are typically 2-3x higher than RD. Note: if the student ranks "
            "QuestBridge partner colleges, she may NOT apply ED/EA/SCEA elsewhere "
            "during the QB Match round; that constraint releases only if she does "
            "not rank QB schools or is not selected as a Finalist."
        ),
        "part5_h1": "Part 5 — Early Action (EA) Options",
        "part5_intro": (
            "EA is non-binding. SCEA / REA schools (Harvard, Yale, Princeton, "
            "Stanford, Notre Dame, Georgetown) are restrictive: they prohibit other "
            "private-school early applications. Unrestricted EA at most publics and "
            "some privates is QuestBridge-compatible only under specific QB rules "
            "(non-binding + home-state public, or required for scholarship "
            "consideration)."
        ),
        "part6_h1": "Part 6 — What to Focus On Between Now and Deadlines",

        # ─── Tier headings ───
        "tier_reach": "Reach",
        "tier_match": "Match",
        "tier_safety": "Safety",
        "tier_heading_n_schools": "{icon} {tier} Tier — {n} Schools",
        "tier_heading_state": "{icon} {tier} Tier — {state}",
        "tier_no_schools": "No schools in this tier.",
        "tier_no_early": "No schools in this list.",

        # ─── Table column headers ───
        "col_num": "#",
        "col_school": "School",
        "col_state": "State",
        "col_odds": "Est. Odds",
        "col_ed_round": "ED Round",
        "col_ea_type": "EA Type",

        # ─── ED / EA round labels ───
        "round_ed": "ED",
        "round_ea": "EA",
        "round_rea_scea": "REA / SCEA",

        # ─── Glossary ───
        "glossary_h1": "Appendix — Abbreviation Glossary",
        "glossary_term_header": "Term",
        "glossary_definition_header": "Definition",

        # ─── Closing line ───
        "closing_line": (
            "Prepared by a U.S. College Admissions Counselor   ·   "
            "For {track} applicant {name}   ·   {ay}"
        ),
        "closing_default_track": "Pre-Health",
        "ay_template": "AY {y0}-{y1}",
    },

    "ko": {
        # ─── 페이지 헤더 / 푸터 ───
        "page_header_template": "{name} — 대학 지원 전략 리포트",
        "page_footer_page_prefix": "페이지 ",
        "page_footer_of": " / ",

        # ─── 제목 블록 ───
        "report_title": "대학 지원 전략 리포트",
        "subtitle_qb_track": "QuestBridge 트랙 지원자용 맞춤 리포트",
        "subtitle_default": "개인 맞춤 Reach / Match / Safety 단계별 리스트",

        # ─── 학생 프로필 요약 ───
        "profile_h1": "학생 프로필 요약",
        "profile_metric_header": "항목",
        "profile_value_header": "내용",
        "profile_label_high_school": "고등학교",
        "profile_label_intended_track": "희망 진로",
        "profile_label_uw_gpa": "UW GPA",
        "profile_label_w_gpa": "W GPA",
        "profile_label_class_rank": "학급 석차",
        "profile_label_sat": "SAT",
        "profile_label_sat_value": "{total}점 (EBRW {ebrw} / Math {math})",
        "profile_label_act": "ACT",
        "profile_label_ap_ib_de": "AP / IB / DE",
        "profile_label_awards": "수상 내역",
        "profile_label_service": "봉사 활동",
        "profile_label_leadership": "리더십",
        "profile_label_program": "지원 프로그램",
        "profile_value_questbridge_planned": "QuestBridge 지원 예정",
        "profile_courses_unit": "{n}과목",
        "profile_hours_unit": "{n}시간 이상",
        "profile_positions_unit": "{n}개 직책",
        "profile_value_dash": "—",

        # ─── 합격률 산정 방식 안내 ───
        "note_h1": "합격률 산정 방식 안내",
        "note_intro": (
            "각 대학 옆에 표시된 백분율은 그 대학의 공식 발표 전체 합격률이 "
            "아닙니다. 다음 요소들을 종합한 **학생 프로필 기반 추정 합격률**입니다:"
        ),
        "note_bullet_cds": (
            "각 대학이 가장 최근에 공개한 Common Data Set(CDS) / 입학 데이터"
        ),
        "note_bullet_sat_gap": (
            "{name} 학생의 {sat_token}과 해당 대학의 중간 50% SAT 구간의 차이"
        ),
        "note_bullet_gpa_rank": (
            "{name} 학생의 GPA·학급 석차를 합격생 평균과 비교"
        ),
        "note_bullet_premed": (
            "Pre-Med(또는 희망 전공) 풀의 경쟁 강도 — 일반 풀보다 훨씬 포화 상태인 경우가 많음"
        ),
        "note_bullet_qb": (
            "QuestBridge Finalist 보너스(QB 파트너 학교는 Finalist 선정 시 "
            "실제 합격 확률이 2-4배 상승)"
        ),
        "note_bullet_hooks": (
            "Hooks: 동문 자녀(legacy), 운동 특기자, 관심 표명(demonstrated interest)을 평가하는 학교의 경우"
        ),
        "note_bullet_sffa": (
            "Post-SFFA 환경(인종 고려 입학이 더 이상 허용되지 않음 — 최상위 명문대에서 "
            "아시아계 지원자에게 미치는 영향은 소폭 긍정적)"
        ),
        "note_bullet_oos": "최상위 주립대(public flagship)에서 아시아계·OOS(타주) 풀의 수요 압박",
        "note_band_line": "Reach = ~20% 이하   ·   Match = ~20-55%   ·   Safety = ~60% 이상",
        "note_warn_sat": (
            "⚠ SAT {sat}점은 상위권 리스트에서 가장 큰 약점입니다. "
            "{name} 학생이 8-9월에 재시험을 봐서 1480점 이상(특히 EBRW)을 만들면 "
            "대부분의 'Reach' 학교 합격률이 한 단계씩 상승합니다. "
            "현재 리스트는 SAT {sat}점 기준입니다."
        ),
        "sat_token_with_value": "SAT {val}점",
        "sat_token_default": "현재 SAT 점수",

        # ─── Part 1-6 ───
        "part1_h1": "1부 — 전국 대학 리스트 (거주 주의 모든 대학 — LAC 포함 — 제외)",
        "part2_h1": "2부 — 전국 LAC 대학 리스트 (거주 주 LAC만 제외)",
        "part2_intro": (
            "LAC는 Pre-Med 지원자에게 전략적으로 중요한 카테고리입니다. "
            "강력한 학생 어드바이징, 소규모 강의, 그리고 — 결정적으로 — 높은 "
            "QuestBridge 파트너십 비율 때문입니다. 거주 주에 위치한 LAC는 "
            "이 섹션이 아니라 3부(거주 주 대학)에 함께 표시됩니다. "
            "⭐ QB는 QuestBridge National College Match 파트너 대학 표시입니다."
        ),
        "part3_h1": "3부 — {state} 거주 주 대학 리스트 (LAC 포함)",
        "part3_intro": (
            "{state} 주의 모든 대학(LAC 포함)이 여기에 정리됩니다. "
            "LAC인 학교는 학교명 옆에 \"(LAC)\" 표시가 붙습니다. "
            "거주 주이므로 in-state 학비와 주(state) 장학금 자격이 가장 중요한 "
            "실용적 동인입니다."
        ),
        "part4_h1": "4부 — Early Decision (ED) 옵션",
        "part4_intro": (
            "ED는 구속력이 있습니다(matched 시 반드시 등록해야 함). ED 라운드 "
            "합격률은 일반적으로 RD의 2-3배입니다. 주의: QuestBridge 파트너 "
            "대학을 ranking 한 경우, QB Match 라운드 동안 다른 학교에 ED/EA/SCEA "
            "지원이 불가능합니다. 이 제약은 QB 학교를 ranking 하지 않거나 "
            "Finalist에 선정되지 않은 경우에만 풀립니다."
        ),
        "part5_h1": "5부 — Early Action (EA) 옵션",
        "part5_intro": (
            "EA는 구속력이 없습니다. 단, SCEA / REA 학교(Harvard, Yale, Princeton, "
            "Stanford, Notre Dame, Georgetown)는 다른 사립대 early 지원을 금지하는 "
            "제한적 EA입니다. 대부분의 주립대와 일부 사립대의 unrestricted EA는 "
            "QuestBridge와 호환 가능하지만, 특정 QB 규칙(non-binding + 거주 주 "
            "public, 또는 장학금 심사 필수) 하에서만 허용됩니다."
        ),
        "part6_h1": "6부 — 지금부터 지원 마감일까지 집중해야 할 사항",

        # ─── 단계 (Tier) ───
        "tier_reach": "Reach (도전권)",
        "tier_match": "Match (적정권)",
        "tier_safety": "Safety (안정권)",
        "tier_heading_n_schools": "{icon} {tier} — {n}개 학교",
        "tier_heading_state": "{icon} {tier} — {state}",
        "tier_no_schools": "이 단계에 해당하는 학교 없음.",
        "tier_no_early": "이 리스트에 해당하는 학교 없음.",

        # ─── 표 헤더 ───
        "col_num": "번호",
        "col_school": "대학",
        "col_state": "주",
        "col_odds": "추정 합격률",
        "col_ed_round": "ED 라운드",
        "col_ea_type": "EA 유형",

        # ─── ED / EA 라운드 표시 ───
        "round_ed": "ED",
        "round_ea": "EA",
        "round_rea_scea": "REA / SCEA",

        # ─── 부록 ───
        "glossary_h1": "부록 — 약어 사전",
        "glossary_term_header": "약어",
        "glossary_definition_header": "의미",

        # ─── 마무리 라인 ───
        "closing_line": (
            "미국 대학 입시 카운슬러 작성   ·   {track} 지원자 {name}   ·   {ay}"
        ),
        "closing_default_track": "Pre-Health",
        "ay_template": "{y0}-{y1} 학년도",
    },
}


def s(lang: Lang, key: str, **fmt) -> str:
    """Look up a string and format it with the given keyword arguments."""
    template = STRINGS[lang][key]
    return template.format(**fmt) if fmt else template
