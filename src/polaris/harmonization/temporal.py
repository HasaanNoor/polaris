"""Calendar-year normalization for harmonized country-year records."""

from __future__ import annotations

import re

YEAR_PATTERN = re.compile(r"^\d{4}$")
RANGE_PATTERN = re.compile(r"^\d{4}\s*[-/]\s*\d{2,4}$")


def normalize_year(value: object) -> int | None:
    """Return an integer calendar year only when the value is annual and explicit."""

    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if 1800 <= value <= 2200 else None
    if isinstance(value, float):
        if value.is_integer():
            year = int(value)
            return year if 1800 <= year <= 2200 else None
        return None
    text = str(value).strip()
    if not text or RANGE_PATTERN.match(text):
        return None
    if not YEAR_PATTERN.match(text):
        return None
    year = int(text)
    return year if 1800 <= year <= 2200 else None
