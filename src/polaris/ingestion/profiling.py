"""Deterministic structural profiling for normalized records."""

from collections import Counter
from datetime import date, datetime

from polaris.ingestion.models import (
    ColumnMapping,
    DataQualityProfile,
    NormalizedRecord,
    ValidationFinding,
    ValidationFindingCode,
    VariableQualityProfile,
)
from polaris.schemas.common import VariableRole
from polaris.schemas.dataset import DatasetManifest


def build_quality_profile(
    manifest: DatasetManifest,
    mappings: tuple[ColumnMapping, ...],
    records: tuple[NormalizedRecord, ...],
    findings: tuple[ValidationFinding, ...],
    *,
    source_row_count: int,
    rejected_row_count: int,
) -> DataQualityProfile:
    """Build deterministic non-analytical data-quality metrics."""

    variable_by_id = {variable.variable_id: variable for variable in manifest.variables}
    invalid_counts = Counter(
        finding.variable_id
        for finding in findings
        if finding.code is ValidationFindingCode.INVALID_VALUE_TYPE
        and finding.variable_id is not None
    )
    profiles: list[VariableQualityProfile] = []

    for mapping in mappings:
        values = tuple(record.values[mapping.variable_id] for record in records)
        non_null_values = tuple(value for value in values if value is not None)
        profiles.append(
            VariableQualityProfile(
                variable_id=mapping.variable_id,
                source_column=mapping.source_column,
                data_type=variable_by_id[mapping.variable_id].data_type.value,
                non_null_count=len(non_null_values),
                null_count=len(values) - len(non_null_values),
                invalid_value_count=invalid_counts[mapping.variable_id],
                unique_value_count=len(set(non_null_values)),
                minimum=_minimum(non_null_values),
                maximum=_maximum(non_null_values),
                observed_types=tuple(sorted({type(value).__name__ for value in non_null_values})),
            )
        )

    return DataQualityProfile(
        dataset_id=manifest.dataset_id,
        row_count=source_row_count,
        accepted_row_count=len(records),
        rejected_row_count=rejected_row_count,
        duplicate_record_count=_duplicate_record_count(manifest, records),
        variables=tuple(profiles),
    )


def _minimum(values: tuple[object, ...]) -> int | float | str | None:
    comparable = _comparable_values(values)
    if not comparable:
        return None
    return _profile_value(min(comparable))


def _maximum(values: tuple[object, ...]) -> int | float | str | None:
    comparable = _comparable_values(values)
    if not comparable:
        return None
    return _profile_value(max(comparable))


def _comparable_values(values: tuple[object, ...]) -> tuple[int | float | date | datetime, ...]:
    if not values:
        return ()
    if all(isinstance(value, bool) for value in values):
        return ()
    if all(isinstance(value, int | float) and not isinstance(value, bool) for value in values):
        return values  # type: ignore[return-value]
    if all(isinstance(value, date | datetime) for value in values):
        return values  # type: ignore[return-value]
    return ()


def _profile_value(value: int | float | date | datetime) -> int | float | str:
    if isinstance(value, date | datetime):
        return value.isoformat()
    return value


def _duplicate_record_count(
    manifest: DatasetManifest,
    records: tuple[NormalizedRecord, ...],
) -> int:
    identifier_ids = tuple(
        variable.variable_id
        for variable in manifest.variables
        if variable.role is VariableRole.IDENTIFIER
    )
    if not identifier_ids:
        return 0
    keys = [
        tuple(record.values.get(variable_id) for variable_id in identifier_ids)
        for record in records
    ]
    counts = Counter(keys)
    return sum(count - 1 for count in counts.values() if count > 1)
