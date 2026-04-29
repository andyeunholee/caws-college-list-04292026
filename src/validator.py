"""Cross-check Claude-generated college rows against the Elite grounding corpus."""

from __future__ import annotations

from rapidfuzz import fuzz, process

from .grounding import EliteCorpus
from .schema import CollegeRow, ValidationFlag


_FUZZ_THRESHOLD = 88


def _best_match(name: str, candidates: list[str]) -> tuple[str, float] | None:
    if not candidates:
        return None
    result = process.extractOne(name, candidates, scorer=fuzz.WRatio)
    if result is None:
        return None
    matched_name, score = result[0], result[1]
    return matched_name, score


def cross_check(rows: list[CollegeRow], corpus: EliteCorpus) -> list[ValidationFlag]:
    """Return flags for any row whose name/state/ED/EA disagrees with the Elite corpus.

    Flags are advisory — never silently drop rows. Rows missing from the corpus get
    an `info` flag (Claude may legitimately recommend colleges outside the dataset).
    """
    flags: list[ValidationFlag] = []
    if not rows:
        return flags

    candidate_names = list(corpus.by_name.keys())

    for row in rows:
        direct = corpus.get(row.name)
        if direct is None:
            best = _best_match(row.name, candidate_names)
            if best and best[1] >= _FUZZ_THRESHOLD:
                matched = corpus.by_name[best[0]]
                if matched.name != row.name:
                    flags.append(
                        ValidationFlag(
                            college_name=row.name,
                            issue=f"Name not exact match in dataset; closest: '{matched.name}' (score {best[1]:.0f}).",
                            severity="info",
                        )
                    )
                direct = matched
            else:
                flags.append(
                    ValidationFlag(
                        college_name=row.name,
                        issue="Not found in Elite dataset (no fuzzy match). Verify the school exists.",
                        severity="warning",
                    )
                )
                continue

        if direct.state and row.state and direct.state.upper() != row.state.upper():
            flags.append(
                ValidationFlag(
                    college_name=row.name,
                    issue=f"State mismatch: row says '{row.state}', dataset says '{direct.state}'.",
                    severity="warning",
                )
            )

        if direct.has_ed is not None and row.has_ed is not None and bool(direct.has_ed) != bool(row.has_ed):
            flags.append(
                ValidationFlag(
                    college_name=row.name,
                    issue=f"ED flag mismatch: row={row.has_ed}, dataset={direct.has_ed}.",
                    severity="warning",
                )
            )

        if direct.has_ea is not None and row.has_ea is not None and bool(direct.has_ea) != bool(row.has_ea):
            flags.append(
                ValidationFlag(
                    college_name=row.name,
                    issue=f"EA flag mismatch: row={row.has_ea}, dataset={direct.has_ea}.",
                    severity="warning",
                )
            )

    return flags
