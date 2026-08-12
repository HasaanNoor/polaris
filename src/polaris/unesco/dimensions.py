"""Reviewed dimension parsing for UNESCO UIS SDG indicator IDs and labels."""

from __future__ import annotations

SEX_SUFFIXES = {".F": "female", ".M": "male", ".GPIA": "gender parity index"}
LOCATION_TOKENS = {".RUR": "rural", ".URB": "urban", ".RURAL": "rural", ".URBAN": "urban"}
WEALTH_TOKENS = {
    ".Q1": "poorest quintile",
    ".Q2": "second quintile",
    ".Q3": "middle quintile",
    ".Q4": "fourth quintile",
    ".Q5": "richest quintile",
}


def sex_dimension(indicator_id: str, label: str) -> str | None:
    for suffix, value in SEX_SUFFIXES.items():
        if indicator_id.endswith(suffix) or f"{suffix}." in indicator_id:
            return value
    if "both sexes" in label.casefold():
        return "both sexes"
    return None


def age_dimension(indicator_id: str, label: str) -> str | None:
    if "AG15T24" in indicator_id:
        return "15-24 years"
    if "AG15T99" in indicator_id:
        return "15+ years"
    if "AG25T99" in indicator_id:
        return "25+ years"
    if "primary school age" in label.casefold():
        return "primary school age"
    if "lower secondary school age" in label.casefold():
        return "lower secondary school age"
    return None


def education_level_dimension(indicator_id: str, label: str) -> str | None:
    text = label.casefold()
    if "pre-primary" in text or indicator_id.startswith("NER.02"):
        return "pre-primary"
    if "primary education" in text or indicator_id.endswith(".1") or ".1." in indicator_id:
        return "primary"
    if "lower secondary" in text or indicator_id.endswith(".2") or ".2." in indicator_id:
        return "lower secondary"
    if "upper secondary" in text or indicator_id.endswith(".3") or ".3." in indicator_id:
        return "upper secondary"
    if "tertiary" in text or "5T8" in indicator_id:
        return "tertiary"
    return None


def location_dimension(indicator_id: str, label: str) -> str | None:
    for token, value in LOCATION_TOKENS.items():
        if token in indicator_id:
            return value
    text = label.casefold()
    if " rural" in text:
        return "rural"
    if " urban" in text:
        return "urban"
    return None


def wealth_dimension(indicator_id: str, label: str) -> str | None:
    for token, value in WEALTH_TOKENS.items():
        if token in indicator_id:
            return value
    text = label.casefold()
    for value in WEALTH_TOKENS.values():
        if value in text:
            return value
    return None


def unit_from_label(label: str) -> str:
    if "(%)" in label:
        return "percent"
    if "gender parity index" in label.casefold() or "gpi" in label.casefold():
        return "parity index"
    if "ratio" in label.casefold():
        return "ratio"
    if "(number)" in label.casefold():
        return "number"
    return "provider value"


def is_headline_both_sexes(indicator_id: str, label: str) -> bool:
    sex = sex_dimension(indicator_id, label)
    return (
        sex not in {"female", "male", "gender parity index"}
        and location_dimension(indicator_id, label) is None
        and wealth_dimension(indicator_id, label) is None
        and "disabled" not in label.casefold()
        and "immigrant" not in label.casefold()
    )
