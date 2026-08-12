"""Schema profiling for local UNESCO UIS files."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

from polaris.harmonization.countries import normalize_country_identifier
from polaris.harmonization.models import GeographicEntityType
from polaris.ingestion.loader import calculate_sha256
from polaris.unesco.catalog import dataset_paths, load_indicator_labels
from polaris.unesco.dimensions import (
    age_dimension,
    education_level_dimension,
    location_dimension,
    sex_dimension,
    unit_from_label,
    wealth_dimension,
)
from polaris.unesco.models import UNESCOEducationSuitability, UNESCOIndicatorProfile


def load_unesco_rows(source_path: str | Path) -> tuple[dict[str, str], ...]:
    with Path(source_path).open(newline="", encoding="utf-8-sig") as file:
        return tuple(csv.DictReader(file))


def profile_unesco_indicator(
    *,
    raw_root: str | Path = "data/raw/unesco",
    dataset: str,
    indicator_id: str,
) -> UNESCOIndicatorProfile:
    paths = dataset_paths(raw_root=raw_root)[dataset]
    labels = load_indicator_labels(raw_root=raw_root).get(dataset, {})
    label = labels.get(indicator_id, indicator_id)
    rows = [
        row for row in load_unesco_rows(paths["data"]) if row.get("INDICATOR_ID") == indicator_id
    ]
    checksum = calculate_sha256(paths["data"])
    country_codes: set[str] = set()
    aggregate_count = 0
    years: list[int] = []
    missing_count = 0
    for row in rows:
        country = normalize_country_identifier(row.get("COUNTRY_ID"), provider="unesco")
        if country.entity_type is GeographicEntityType.SOVEREIGN_COUNTRY:
            country_codes.add(str(country.canonical_code))
        else:
            aggregate_count += 1
        year = _safe_year(row.get("YEAR"))
        if year is not None:
            years.append(year)
        if row.get("VALUE") in {None, ""}:
            missing_count += 1
    duplicates = Counter(
        (row.get("COUNTRY_ID"), row.get("YEAR"))
        for row in rows
        if row.get("COUNTRY_ID") and row.get("YEAR")
    )
    duplicate_count = sum(1 for count in duplicates.values() if count > 1)
    schema_findings = _schema_findings(rows)
    return UNESCOIndicatorProfile(
        source_dataset=dataset,
        source_file=str(paths["data"]),
        source_checksum=checksum,
        unesco_indicator_id=indicator_id,
        official_title=label,
        definition=label,
        unit=unit_from_label(label),
        sex_dimension=sex_dimension(indicator_id, label),
        age_dimension=age_dimension(indicator_id, label),
        education_level_dimension=education_level_dimension(indicator_id, label),
        location_dimension=location_dimension(indicator_id, label),
        wealth_dimension=wealth_dimension(indicator_id, label),
        estimate_status_dimension="modelled data" if "modelled data" in label.casefold() else None,
        country_coverage=len(country_codes),
        temporal_coverage=(min(years), max(years)) if years else None,
        row_count=len(rows),
        missing_value_count=missing_count,
        duplicate_key_findings=(
            (f"{duplicate_count} country-year duplicate keys before review",)
            if duplicate_count
            else ()
        ),
        aggregate_record_count=aggregate_count,
        suitability_classification=_suitability(
            label=label, rows=rows, country_count=len(country_codes)
        ),
        schema_findings=schema_findings,
    )


def profile_candidate_indicators(
    *,
    raw_root: str | Path = "data/raw/unesco",
    dataset: str = "SDG",
    indicator_ids: tuple[str, ...],
) -> tuple[UNESCOIndicatorProfile, ...]:
    return tuple(
        profile_unesco_indicator(raw_root=raw_root, dataset=dataset, indicator_id=indicator_id)
        for indicator_id in indicator_ids
    )


def profile_all_downloaded_datasets(*, raw_root: str | Path = "data/raw/unesco") -> dict[str, Any]:
    profiles: dict[str, Any] = {}
    labels = load_indicator_labels(raw_root=raw_root)
    for dataset, paths in dataset_paths(raw_root=raw_root).items():
        data_path = paths["data"]
        rows = load_unesco_rows(data_path) if data_path.exists() else ()
        years = [_safe_year(row.get("YEAR")) for row in rows]
        valid_years = [year for year in years if year is not None]
        profiles[dataset] = {
            "data_file": str(data_path),
            "row_count": len(rows),
            "indicator_count": len(labels.get(dataset, {})),
            "country_field": "COUNTRY_ID",
            "year_field": "YEAR",
            "numeric_value_field": "VALUE",
            "year_range": [min(valid_years), max(valid_years)] if valid_years else None,
            "checksum_sha256": calculate_sha256(data_path) if data_path.exists() else None,
        }
    return profiles


def _safe_year(value: object) -> int | None:
    text = "" if value is None else str(value).strip()
    return int(text) if text.isdigit() and len(text) == 4 else None


def _schema_findings(rows: list[dict[str, str]]) -> tuple[str, ...]:
    if not rows:
        return ("indicator has no rows in downloaded national data",)
    required = {"INDICATOR_ID", "COUNTRY_ID", "YEAR", "VALUE"}
    observed = set().union(*(row.keys() for row in rows))
    missing = sorted(required - observed)
    return tuple(f"missing required field {field}" for field in missing)


def _suitability(
    *, label: str, rows: list[dict[str, str]], country_count: int
) -> UNESCOEducationSuitability:
    text = label.casefold()
    if any(term in text for term in ("female", "male", "rural", "urban", "quintile")):
        return UNESCOEducationSuitability.LOW
    if "modelled data" in text or country_count < 75:
        return UNESCOEducationSuitability.MEDIUM
    if rows and country_count >= 75:
        return UNESCOEducationSuitability.HIGH
    return UNESCOEducationSuitability.LOW
