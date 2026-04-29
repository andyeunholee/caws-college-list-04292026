"""Pydantic models for student profile, college rows, and tiered output."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict

Scope = Literal["national_excl_home", "in_state", "lac"]
Tier = Literal["reach", "match", "safety"]


class CourseworkItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    type: Optional[str] = None  # AP / IB / DE / Honors / Regular
    grade: Optional[str] = None


class Activity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    role: Optional[str] = None
    years: Optional[str] = None
    hours: Optional[int] = None
    description: Optional[str] = None


class Award(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    level: Optional[str] = None  # School / Regional / State / National / International
    year: Optional[str] = None


class StudentProfile(BaseModel):
    """Structured student information extracted from a free-form email."""

    model_config = ConfigDict(extra="ignore")

    name: str
    grade: Optional[str] = "12"
    high_school: Optional[str] = None
    state: Optional[str] = Field(
        None, description="Two-letter US state code of the high school, e.g. GA"
    )
    city: Optional[str] = None

    gpa_unweighted: Optional[float] = None
    gpa_weighted: Optional[float] = None
    class_rank: Optional[str] = None  # e.g. "12/450"

    sat_total: Optional[int] = None
    sat_ebrw: Optional[int] = None
    sat_math: Optional[int] = None
    act_composite: Optional[int] = None

    intended_major: Optional[str] = None
    secondary_major: Optional[str] = None
    career_goal: Optional[str] = None  # e.g. "Pre-Med", "Pre-Law"

    coursework: list[CourseworkItem] = Field(default_factory=list)
    activities: list[Activity] = Field(default_factory=list)
    leadership: list[str] = Field(default_factory=list)
    awards: list[Award] = Field(default_factory=list)
    community_service_hours: Optional[int] = None

    target_schools_mentioned: list[str] = Field(default_factory=list)
    questbridge_candidate: Optional[bool] = None
    financial_aid_needed: Optional[bool] = None
    first_gen: Optional[bool] = None
    legacy_at: list[str] = Field(default_factory=list)
    recruited_athlete_sport: Optional[str] = None

    narrative_notes: Optional[str] = None  # free-text observations / strengths / risks
    raw_email_excerpt: Optional[str] = None  # for debugging traceability


class CollegeRow(BaseModel):
    """One college recommendation row."""

    model_config = ConfigDict(extra="ignore")

    name: str
    state: str  # Two-letter US state code
    tier: Tier
    adjusted_probability: float = Field(
        ..., ge=0.0, le=1.0,
        description="Profile-adjusted estimated acceptance probability (0-1).",
    )
    reasoning_factor: str = Field(
        ..., description="One-line explanation of why probability differs from raw rate."
    )
    has_ed: Optional[bool] = None
    has_ea: Optional[bool] = None
    has_rea_or_scea: Optional[bool] = None
    notes: Optional[str] = None


class TieredList(BaseModel):
    """50/50/50 tiered list for a single scope."""

    model_config = ConfigDict(extra="ignore")

    scope: Scope
    reach: list[CollegeRow] = Field(default_factory=list)
    match: list[CollegeRow] = Field(default_factory=list)
    safety: list[CollegeRow] = Field(default_factory=list)

    def all_rows(self) -> list[CollegeRow]:
        return [*self.reach, *self.match, *self.safety]


class CollegeFact(BaseModel):
    """Grounding fact loaded from the Elite US College Data Sheet."""

    model_config = ConfigDict(extra="ignore")

    name: str
    state: Optional[str] = None
    is_lac: bool = False
    acceptance_rate: Optional[float] = None
    sat_total: Optional[int] = None
    act_midpoint: Optional[int] = None
    has_ed: Optional[bool] = None
    has_ea: Optional[bool] = None
    has_rea: Optional[bool] = None
    ed_deadline: Optional[str] = None
    ea_deadline: Optional[str] = None
    rea_deadline: Optional[str] = None
    test_policy: Optional[str] = None
    early_acceptance_rate: Optional[float] = None


class ValidationFlag(BaseModel):
    """Issue raised by the validator after cross-checking a Claude response."""

    model_config = ConfigDict(extra="ignore")

    college_name: str
    issue: str  # e.g. "Name not found in Elite corpus"
    severity: Literal["info", "warning", "error"] = "warning"
