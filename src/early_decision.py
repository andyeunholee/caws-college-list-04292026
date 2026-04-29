"""Split a merged college list into ED-eligible and EA-eligible sub-lists."""

from __future__ import annotations

from .grounding import EliteCorpus, find_by_name
from .schema import CollegeRow


def _truthy(value: bool | None) -> bool:
    return bool(value) if value is not None else False


def _enrich_with_corpus(row: CollegeRow, corpus: EliteCorpus) -> CollegeRow:
    """Fill missing has_ed/has_ea/has_rea flags from the Elite corpus when possible."""
    fact = find_by_name(corpus, row.name)
    if fact is None:
        return row
    updated = row.model_copy(
        update={
            "has_ed": row.has_ed if row.has_ed is not None else fact.has_ed,
            "has_ea": row.has_ea if row.has_ea is not None else fact.has_ea,
            "has_rea_or_scea": row.has_rea_or_scea
            if row.has_rea_or_scea is not None
            else fact.has_rea,
        }
    )
    return updated


def split_ed_ea(
    all_rows: list[CollegeRow], corpus: EliteCorpus
) -> tuple[list[CollegeRow], list[CollegeRow]]:
    """Return (ed_rows, ea_rows). A school can appear in both if it offers ED+EA."""
    seen_ed: set[str] = set()
    seen_ea: set[str] = set()
    ed_rows: list[CollegeRow] = []
    ea_rows: list[CollegeRow] = []

    for raw in all_rows:
        row = _enrich_with_corpus(raw, corpus)
        if _truthy(row.has_ed) and row.name not in seen_ed:
            ed_rows.append(row)
            seen_ed.add(row.name)
        if (_truthy(row.has_ea) or _truthy(row.has_rea_or_scea)) and row.name not in seen_ea:
            ea_rows.append(row)
            seen_ea.add(row.name)

    ed_rows.sort(key=lambda r: -r.adjusted_probability)
    ea_rows.sort(key=lambda r: -r.adjusted_probability)
    return ed_rows, ea_rows
