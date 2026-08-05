"""Discovery and structural inspection for downloaded official datasets."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from polaris.ingestion.loader import calculate_sha256, file_size
from polaris.realdata.models import (
    ColumnProfile,
    DatasetSchemaInspection,
    DiscoveredDataset,
    IdentifierValidation,
)

COUNTRY_COLUMNS = (
    "Country Code",
    "SpatialDimValueCode",
    "COUNTRY_ID",
    "REF_AREA",
    "location",
    "country_code",
)
YEAR_COLUMNS = ("Year", "Period", "YEAR", "TIME_PERIOD", "period")
NULL_TOKENS = {"", "null", "NULL", "NA", "N/A", ".."}


def discover_real_datasets(raw_root: str | Path = "data/raw") -> tuple[DiscoveredDataset, ...]:
    """Discover official CSV datasets downloaded by Phase 10 providers."""

    root = Path(raw_root)
    if not root.exists():
        return ()

    discovered: list[DiscoveredDataset] = []
    wdi = root / "world_bank" / "WDI_CSV" / "WDICSV.csv"
    if wdi.exists():
        discovered.append(_dataset("world_bank", "WDI", wdi, wdi.parent.glob("WDI*.csv")))

    who_root = root / "who"
    if who_root.exists():
        for path in sorted(who_root.glob("*.csv")):
            discovered.append(_dataset("who", path.stem, path, ()))

    unesco_root = root / "unesco"
    if unesco_root.exists():
        for path in sorted(unesco_root.glob("*/*_DATA_*.csv")):
            dataset_key = f"{path.parent.name}_{path.stem.removeprefix(path.parent.name + '_')}"
            discovered.append(_dataset("unesco", dataset_key, path, path.parent.glob("*.csv")))

    return tuple(discovered)


def inspect_schema(path: str | Path, *, max_rows: int | None = 5000) -> DatasetSchemaInspection:
    """Inspect a CSV schema and missingness without changing the source file."""

    source_path = Path(path)
    with source_path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        columns = tuple(reader.fieldnames or ())
        samples: dict[str, list[str]] = {column: [] for column in columns}
        non_null: dict[str, int] = defaultdict(int)
        nulls: dict[str, int] = defaultdict(int)
        uniques: dict[str, set[str]] = {column: set() for column in columns}
        row_count = 0
        for row in reader:
            row_count += 1
            if max_rows is not None and row_count > max_rows:
                break
            for column in columns:
                value = (row.get(column) or "").strip()
                if value in NULL_TOKENS:
                    nulls[column] += 1
                    continue
                non_null[column] += 1
                if len(uniques[column]) < 1000:
                    uniques[column].add(value)
                if len(samples[column]) < 3:
                    samples[column].append(value)

    inspected = row_count if max_rows is None else min(row_count, max_rows)
    profiles = tuple(
        ColumnProfile(
            name=column,
            inferred_type=_infer_type(samples[column]),
            non_null_count=non_null[column],
            null_count=nulls[column],
            unique_count=len(uniques[column]),
            examples=tuple(samples[column]),
        )
        for column in columns
    )
    country_column = _first_present(columns, COUNTRY_COLUMNS)
    year_column = _first_present(columns, YEAR_COLUMNS)
    variable_columns = _variable_columns(columns)
    return DatasetSchemaInspection(
        path=source_path,
        row_count_inspected=inspected,
        total_row_count=None if max_rows is not None and row_count > max_rows else row_count,
        columns=columns,
        column_count=len(columns),
        variable_columns=variable_columns,
        country_identifier=_identifier_validation(country_column, profiles, _valid_country),
        year_identifier=_identifier_validation(year_column, profiles, _valid_year),
        missing_value_counts=tuple((column, nulls[column]) for column in columns),
        column_profiles=profiles,
    )


def _dataset(
    provider: str,
    dataset_key: str,
    path: Path,
    companion_candidates,
) -> DiscoveredDataset:
    companions = tuple(sorted(candidate for candidate in companion_candidates if candidate != path))
    return DiscoveredDataset(
        provider=provider,
        dataset_key=dataset_key,
        path=path,
        companion_files=companions,
        file_size_bytes=file_size(path),
        checksum_sha256=calculate_sha256(path),
    )


def _first_present(columns: tuple[str, ...], candidates: tuple[str, ...]) -> str | None:
    by_lower = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in by_lower:
            return by_lower[candidate.lower()]
    return None


def _variable_columns(columns: tuple[str, ...]) -> tuple[str, ...]:
    if "Indicator Code" in columns:
        return ("Indicator Code",)
    if "IndicatorCode" in columns:
        return ("IndicatorCode", "Indicator")
    if "INDICATOR_ID" in columns:
        return ("INDICATOR_ID", "VALUE")
    id_like = {
        *(column.lower() for column in COUNTRY_COLUMNS),
        *(column.lower() for column in YEAR_COLUMNS),
    }
    return tuple(column for column in columns if column.lower() not in id_like)


def _identifier_validation(
    column: str | None,
    profiles: tuple[ColumnProfile, ...],
    validator,
) -> IdentifierValidation:
    if column is None:
        return IdentifierValidation(present=False, non_null_count=0, invalid_count=0)
    profile = next(item for item in profiles if item.name == column)
    invalid = tuple(value for value in profile.examples if not validator(value))
    return IdentifierValidation(
        column=column,
        present=True,
        non_null_count=profile.non_null_count,
        invalid_count=len(invalid),
        examples=profile.examples,
    )


def _infer_type(values: list[str]) -> str:
    if not values:
        return "empty"
    if all(_valid_int(value) for value in values):
        return "integer"
    if all(_valid_float(value) for value in values):
        return "float"
    return "string"


def _valid_country(value: str) -> bool:
    return bool(value.strip()) and len(value.strip()) <= 12


def _valid_year(value: str) -> bool:
    return _valid_int(value) and 1800 <= int(value) <= 2200


def _valid_int(value: str) -> bool:
    try:
        int(value)
    except ValueError:
        return False
    return True


def _valid_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True
