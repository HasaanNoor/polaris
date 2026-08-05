"""Manifest and variable compatibility checks for real datasets."""

import csv
from pathlib import Path

from polaris.ingestion.loader import calculate_sha256
from polaris.realdata.discovery import inspect_schema
from polaris.realdata.models import ManifestValidationResult, VariableSummary
from polaris.schemas.dataset import DatasetManifest


def validate_manifest_against_file(
    *,
    manifest: DatasetManifest,
    source_path: str | Path,
    manifest_path: str | Path | None = None,
) -> ManifestValidationResult:
    """Validate checksum, access URL, and declared columns against a CSV file."""

    path = Path(source_path)
    inspection = inspect_schema(path)
    source_columns = set(inspection.columns)
    declared = tuple(
        variable.source_field_name or variable.variable_id for variable in manifest.variables
    )
    missing = tuple(column for column in declared if column not in source_columns)
    unexpected = tuple(column for column in inspection.columns if column not in set(declared))
    checksum = calculate_sha256(path)
    return ManifestValidationResult(
        dataset_id=manifest.dataset_id,
        source_path=path,
        manifest_path=Path(manifest_path) if manifest_path is not None else None,
        checksum_matches=manifest.checksum == checksum,
        access_url_matches=manifest.access_url in {None, str(path)},
        missing_manifest_columns=missing,
        unexpected_source_columns=unexpected,
        compatible_with_phase3=not missing,
    )


def variable_summaries(
    manifest: DatasetManifest,
    source_path: str | Path,
) -> tuple[VariableSummary, ...]:
    """Summarize manifest variables using Phase 3 quality profiling inputs."""

    path = Path(source_path)
    inspection = inspect_schema(path, max_rows=None)
    profile_by_column = {profile.name: profile for profile in inspection.column_profiles}
    ranges = _column_ranges(
        path,
        tuple(
            variable.source_field_name or variable.variable_id for variable in manifest.variables
        ),
    )
    summaries: list[VariableSummary] = []
    for variable in manifest.variables:
        source_column = variable.source_field_name or variable.variable_id
        profile = profile_by_column[source_column]
        minimum, maximum = ranges[source_column]
        summaries.append(
            VariableSummary(
                variable_id=variable.variable_id,
                source_field_name=source_column,
                role=variable.role.value,
                data_type=variable.data_type.value,
                non_null_count=profile.non_null_count,
                null_count=profile.null_count,
                unique_count=profile.unique_count,
                minimum=minimum,
                maximum=maximum,
            )
        )
    return tuple(summaries)


def _column_ranges(
    path: Path,
    columns: tuple[str, ...],
) -> dict[str, tuple[float | str | None, float | str | None]]:
    values: dict[str, list[str]] = {column: [] for column in columns}
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            for column in columns:
                value = (row.get(column) or "").strip()
                if value:
                    values[column].append(value)
    return {column: _range(observed) for column, observed in values.items()}


def _range(values: list[str]) -> tuple[float | str | None, float | str | None]:
    if not values:
        return None, None
    parsed: list[float] = []
    for value in values:
        try:
            parsed.append(float(value))
        except ValueError:
            return min(values), max(values)
    return min(parsed), max(parsed)
