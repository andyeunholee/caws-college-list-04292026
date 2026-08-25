"""Loader for the Elite US College Data Sheet → grounding facts for Claude.

Merges:
- college_lists.py (NATIONAL_UNIVERSITIES + LIBERAL_ARTS_COLLEGES) — supplies state codes
- cache/national_scorecard.json + cache/lac_scorecard.json — supplies admit rates / SAT / ACT
- overrides.json — supplies ED/EA/REA availability and deadlines

Produces three scope-specific lists for the generator.
"""

from __future__ import annotations

import importlib.util
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import CollegeFact, Scope
from .utils import logging_ko


@dataclass
class EliteCorpus:
    by_name: dict[str, CollegeFact]

    def get(self, name: str) -> CollegeFact | None:
        return self.by_name.get(name)

    def all(self) -> list[CollegeFact]:
        return list(self.by_name.values())


def _slug_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _load_college_lists(elite_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path = elite_dir / "college_lists.py"
    if not path.exists():
        raise FileNotFoundError(f"college_lists.py not found: {path}")
    spec = importlib.util.spec_from_file_location("elite_college_lists", path)
    if spec is None or spec.loader is None:
        raise ImportError("Failed to load college_lists.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return (
        list(getattr(module, "NATIONAL_UNIVERSITIES", [])),
        list(getattr(module, "LIBERAL_ARTS_COLLEGES", [])),
    )


def _safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        logging_ko.warn(f"{path.name} missing — skipping")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _coerce_rate(value: Any) -> float | None:
    """Convert a percent-style scorecard value (e.g., 4.6) to a 0-1 fraction."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v / 100.0 if v > 1.0 else v


def _coerce_early_rate(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return _coerce_rate(value)
    if isinstance(value, str):
        m = re.search(r"([0-9]+(?:\.[0-9]+)?)", value)
        if m:
            return _coerce_rate(float(m.group(1)))
    return None


def load_elite_dataset(elite_dir: Path) -> EliteCorpus:
    nat_list, lac_list = _load_college_lists(elite_dir)
    nat_card = _safe_load_json(elite_dir / "cache" / "national_scorecard.json").get("data", {})
    lac_card = _safe_load_json(elite_dir / "cache" / "lac_scorecard.json").get("data", {})
    overrides = _safe_load_json(elite_dir / "overrides.json")

    by_name: dict[str, CollegeFact] = {}

    def _ingest(entries: list[dict[str, Any]], cards: dict[str, Any], is_lac: bool) -> None:
        for e in entries:
            name = e.get("name", "").strip()
            if not name:
                continue
            card = cards.get(name, {})
            ov = overrides.get(name, {})
            fact = CollegeFact(
                name=name,
                state=e.get("state"),
                is_lac=is_lac,
                acceptance_rate=_coerce_rate(card.get("acceptance_rate")),
                sat_total=card.get("sat_total"),
                act_midpoint=card.get("act_midpoint"),
                has_ed=ov.get("has_ed"),
                has_ea=ov.get("has_ea"),
                has_rea=ov.get("has_rea"),
                ed_deadline=ov.get("ed_deadline"),
                ea_deadline=ov.get("ea_deadline"),
                rea_deadline=ov.get("rea_deadline"),
                test_policy=ov.get("test_policy") or e.get("test_policy"),
                early_acceptance_rate=_coerce_early_rate(ov.get("early_acceptance_rate")),
            )
            by_name[name] = fact

    _ingest(nat_list, nat_card, is_lac=False)
    _ingest(lac_list, lac_card, is_lac=True)

    logging_ko.info(f"Elite dataset loaded: {len(by_name)} colleges")
    return EliteCorpus(by_name=by_name)


def curate_for_scope(
    corpus: EliteCorpus, scope: Scope, home_state: str | None
) -> list[CollegeFact]:
    """Filter the Elite corpus down to one scope.

    Scope semantics (updated):
    - "national_excl_home": national universities (non-LAC) located OUTSIDE the
      student's home state. Home-state colleges (both LAC and non-LAC) are
      excluded entirely from this list.
    - "lac": Liberal Arts Colleges nationwide, EXCLUDING home-state LACs.
    - "in_state": ALL colleges in the home state (both LAC and non-LAC).
    """
    home = (home_state or "").upper().strip()
    out: list[CollegeFact] = []
    for fact in corpus.all():
        is_home = bool(home and fact.state and fact.state.upper() == home)
        if scope == "national_excl_home":
            if fact.is_lac:
                continue
            if is_home:
                continue
            out.append(fact)
        elif scope == "in_state":
            if is_home:
                out.append(fact)
        elif scope == "lac":
            if fact.is_lac and not is_home:
                out.append(fact)
    out.sort(key=lambda f: (f.acceptance_rate or 1.0))
    return out


def find_by_name(corpus: EliteCorpus, name: str) -> CollegeFact | None:
    """Best-effort name match (exact, then slug-equivalent)."""
    direct = corpus.by_name.get(name)
    if direct is not None:
        return direct
    target = _slug_key(name)
    for fact in corpus.all():
        if _slug_key(fact.name) == target:
            return fact
    return None
