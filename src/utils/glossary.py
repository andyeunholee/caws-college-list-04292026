"""Definitions of the abbreviations that appear in the final document."""

from __future__ import annotations

from typing import Literal

Lang = Literal["en", "ko"]


GLOSSARY: list[tuple[str, str]] = [
    ("ED", "Early Decision — Binding early-application plan. If admitted, the student must enroll and withdraw all other applications. Typically a November 1 or November 15 deadline."),
    ("ED II", "Early Decision Round 2 — A second binding ED window, usually in early January, offered by some schools as a follow-up to RD."),
    ("EA", "Early Action — Non-binding early application. Decisions arrive in December/January but the student is not committed to enroll."),
    ("REA", "Restrictive Early Action — Non-binding but limits the student from applying ED elsewhere. Used by Stanford, Yale, Princeton, Notre Dame."),
    ("SCEA", "Single-Choice Early Action — Functionally equivalent to REA. Used by Harvard."),
    ("RD", "Regular Decision — Standard application cycle, deadlines typically January 1-15, decisions in March/April."),
    ("Rolling", "Rolling Admissions — Applications evaluated as they arrive until the class fills."),
    ("HPAC", "Health Professions Advisory Committee — College-level body that interviews and writes a composite letter for medical/health professional school applicants."),
    ("MCAT", "Medical College Admission Test — Standardized exam required for U.S. medical school admission."),
    ("LAC", "Liberal Arts College — Small undergraduate-focused institution emphasizing breadth across humanities, sciences, and social sciences."),
    ("AP", "Advanced Placement — College-level coursework and exams administered by the College Board to U.S. high schoolers."),
    ("IB", "International Baccalaureate — A globally recognized rigorous secondary curriculum culminating in the IB Diploma."),
    ("DE", "Dual Enrollment — High school students taking courses at a college or university for simultaneous high-school and college credit."),
    ("UW GPA", "Unweighted GPA — GPA calculated on a 4.0 scale with no extra weight for AP/IB/Honors."),
    ("W GPA", "Weighted GPA — GPA that gives extra credit (often 0.5 or 1.0) for honors-level courses."),
    ("EBRW", "Evidence-Based Reading and Writing — One of the two main sections of the SAT (200-800)."),
    ("FAFSA", "Free Application for Federal Student Aid — Federal financial-aid form required for U.S. need-based aid."),
    ("CSS Profile", "College Scholarship Service Profile — Supplemental financial-aid form used by ~250 selective colleges, primarily for institutional aid."),
    ("QuestBridge", "QuestBridge National College Match — A program that matches high-achieving low-income students to ~50 partner colleges with binding full-ride scholarship offers."),
    ("URM", "Underrepresented Minority — Demographic groups historically underrepresented in higher education."),
    ("Holistic Review", "Admissions process considering academics, activities, essays, recommendations, and context together rather than by formula."),
    ("Demonstrated Interest", "Signals to a college that a student is genuinely interested (campus visits, info sessions, opening emails)."),
    ("Yield", "Percentage of admitted students who enroll. Higher yield often correlates with stricter admission standards."),
    ("In-State Tuition", "Reduced tuition rate offered by public universities to legal residents of the state."),
    ("Out-of-State Tuition", "Higher tuition charged at public universities to non-residents."),
]


GLOSSARY_KO: list[tuple[str, str]] = [
    ("ED", "Early Decision — 구속력 있는 조기 지원. 합격하면 반드시 등록하고 다른 모든 지원을 철회해야 함. 보통 11월 1일 또는 11월 15일 마감."),
    ("ED II", "Early Decision Round 2 — 일부 대학이 운영하는 두 번째 ED 라운드. 보통 1월 초 마감, 첫 ED 시즌에 결정 못한 학생용."),
    ("EA", "Early Action — 비구속 조기 지원. 12월~1월에 결과가 나오지만 등록 의무는 없음."),
    ("REA", "Restrictive Early Action — 비구속이지만 다른 사립대 ED·EA 지원을 제한. Stanford·Yale·Princeton·Notre Dame이 사용."),
    ("SCEA", "Single-Choice Early Action — REA와 사실상 동일. Harvard가 사용."),
    ("RD", "Regular Decision — 일반 지원 라운드. 마감 보통 1월 1-15일, 결과 3-4월 발표."),
    ("Rolling", "Rolling Admissions — 정원이 찰 때까지 도착하는 순서대로 심사하는 방식."),
    ("HPAC", "Health Professions Advisory Committee — 의대·치대 등 보건 전문직 진학 지원자에게 통합 추천서를 작성해주는 학부 단위 기구."),
    ("MCAT", "Medical College Admission Test — 미국 의과대학 입학을 위한 표준화 시험."),
    ("LAC", "Liberal Arts College — 학부 중심의 소규모 대학. 인문·사회·자연과학을 두루 가르치는 교양 중심 교육."),
    ("AP", "Advanced Placement — College Board가 운영하는 미국 고등학생용 대학 수준 과목 및 시험."),
    ("IB", "International Baccalaureate — 전 세계적으로 인정받는 국제 대학 예비 교육 과정."),
    ("DE", "Dual Enrollment — 고등학생이 대학 강의를 들으며 고교·대학 학점을 동시에 취득하는 제도."),
    ("UW GPA", "Unweighted GPA — Honors·AP·IB 가산점 없이 4.0 만점 기준으로 계산한 GPA."),
    ("W GPA", "Weighted GPA — Honors·AP·IB 과목에 가산점(보통 +0.5 또는 +1.0)을 적용한 GPA."),
    ("EBRW", "Evidence-Based Reading and Writing — SAT의 영어 영역(200-800점)."),
    ("FAFSA", "Free Application for Federal Student Aid — 미국 연방 학자금 지원 신청서."),
    ("CSS Profile", "College Scholarship Service Profile — 약 250개 사립 명문대가 사용하는 추가 재정 지원 신청서."),
    ("QuestBridge", "QuestBridge National College Match — 저소득·고성취 학생을 약 50개 파트너 대학과 매칭해 4년 전액 장학금을 제공하는 프로그램."),
    ("URM", "Underrepresented Minority — 고등 교육에서 역사적으로 과소대표된 인종·민족 집단."),
    ("Holistic Review", "지원자의 학업·활동·에세이·추천서·맥락을 공식이 아닌 종합적으로 평가하는 입학 심사 방식."),
    ("Demonstrated Interest", "학생이 그 대학에 진심으로 관심 있음을 보여주는 신호(캠퍼스 방문, 정보 세션, 이메일 열람 등)."),
    ("Yield", "합격생 중 실제 등록한 학생의 비율. yield가 높을수록 해당 대학의 위상이 높다고 볼 수 있음."),
    ("In-State Tuition", "거주 주의 주립대학이 그 주 거주자에게 제공하는 할인된 학비."),
    ("Out-of-State Tuition", "주립대학이 타주 거주자에게 부과하는 더 높은 학비."),
]


def get_glossary(lang: Lang) -> list[tuple[str, str]]:
    return GLOSSARY_KO if lang == "ko" else GLOSSARY
