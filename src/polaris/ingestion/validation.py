"""Manifest-to-file structural validation for local ingestion."""

from collections import Counter

from polaris.ingestion.models import (
    ColumnMapping,
    IngestionConfiguration,
    LoadedTabularFile,
    UnexpectedColumnMode,
    ValidationFinding,
    ValidationFindingCode,
    ValidationSeverity,
)
from polaris.schemas.dataset import DatasetManifest, DatasetVariable


def map_manifest_columns(
    manifest: DatasetManifest,
    loaded_file: LoadedTabularFile,
    configuration: IngestionConfiguration,
) -> tuple[
    tuple[ColumnMapping, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[ValidationFinding, ...],
]:
    """Map source columns to manifest variables using exact declared identifiers."""

    findings: list[ValidationFinding] = []
    source_columns = loaded_file.source_columns
    source_path = loaded_file.source_path

    if not source_columns:
        findings.append(
            ValidationFinding(
                severity=ValidationSeverity.FATAL,
                code=ValidationFindingCode.EMPTY_DATASET,
                message="source file has no header row",
                source_path=source_path,
            )
        )

    for column in source_columns:
        if column == "":
            findings.append(
                ValidationFinding(
                    severity=ValidationSeverity.ERROR,
                    code=ValidationFindingCode.INVALID_MANIFEST_DECLARATION,
                    message="source header contains an empty column name",
                    source_path=source_path,
                    source_column=column,
                )
            )

    duplicate_source_columns = _duplicates(source_columns)
    findings.extend(
        ValidationFinding(
            severity=ValidationSeverity.ERROR,
            code=ValidationFindingCode.DUPLICATE_COLUMN,
            message=f'duplicate source column "{column}"',
            source_path=source_path,
            source_column=column,
        )
        for column in duplicate_source_columns
    )

    variable_ids = tuple(variable.variable_id for variable in manifest.variables)
    for variable_id in _duplicates(variable_ids):
        findings.append(
            ValidationFinding(
                severity=ValidationSeverity.ERROR,
                code=ValidationFindingCode.INVALID_MANIFEST_DECLARATION,
                message=f'duplicate manifest variable_id "{variable_id}"',
                source_path=source_path,
                variable_id=variable_id,
            )
        )

    desired_columns = tuple(_declared_source_name(variable) for variable in manifest.variables)
    for column in _duplicates(desired_columns):
        affected = tuple(
            variable.variable_id
            for variable in manifest.variables
            if _declared_source_name(variable) == column
        )
        findings.append(
            ValidationFinding(
                severity=ValidationSeverity.ERROR,
                code=ValidationFindingCode.AMBIGUOUS_COLUMN_MAPPING,
                message=(
                    f'manifest maps multiple variables to source column "{column}": '
                    + ", ".join(affected)
                ),
                source_path=source_path,
                source_column=column,
            )
        )

    source_index = {column: index for index, column in enumerate(source_columns)}
    mappings: list[ColumnMapping] = []
    missing_columns: list[str] = []
    for variable in manifest.variables:
        declared_name = _declared_source_name(variable)
        if declared_name not in source_index:
            missing_columns.append(declared_name)
            findings.append(
                ValidationFinding(
                    severity=ValidationSeverity.ERROR,
                    code=ValidationFindingCode.MISSING_REQUIRED_COLUMN,
                    message=(
                        f'required source column "{declared_name}" is missing for '
                        f'variable "{variable.variable_id}"'
                    ),
                    source_path=source_path,
                    source_column=declared_name,
                    variable_id=variable.variable_id,
                )
            )
            continue
        mappings.append(
            ColumnMapping(
                variable_id=variable.variable_id,
                source_column=declared_name,
                source_index=source_index[declared_name],
            )
        )

    mapped_columns = {mapping.source_column for mapping in mappings}
    unexpected_columns = tuple(column for column in source_columns if column not in mapped_columns)
    unexpected_severity = (
        ValidationSeverity.ERROR
        if configuration.unexpected_column_mode is UnexpectedColumnMode.STRICT
        else ValidationSeverity.WARNING
    )
    findings.extend(
        ValidationFinding(
            severity=unexpected_severity,
            code=ValidationFindingCode.UNEXPECTED_COLUMN,
            message=f'unexpected source column "{column}" is not declared by the manifest',
            source_path=source_path,
            source_column=column,
        )
        for column in unexpected_columns
    )

    findings.extend(
        ValidationFinding(
            severity=ValidationSeverity.ERROR,
            code=ValidationFindingCode.MALFORMED_ROW,
            message=(f"row has {len(row.values)} fields but header declares {len(source_columns)}"),
            source_path=source_path,
            row_number=row.row_number,
        )
        for row in loaded_file.malformed_rows
    )

    if not loaded_file.rows and not loaded_file.malformed_rows and source_columns:
        findings.append(
            ValidationFinding(
                severity=ValidationSeverity.WARNING,
                code=ValidationFindingCode.EMPTY_DATASET,
                message="source file has a header row but no data rows",
                source_path=source_path,
            )
        )

    return (
        tuple(mappings),
        tuple(dict.fromkeys(missing_columns)),
        unexpected_columns,
        tuple(findings),
    )


def mapping_by_variable(mappings: tuple[ColumnMapping, ...]) -> dict[str, ColumnMapping]:
    """Return mappings keyed by canonical variable id."""

    return {mapping.variable_id: mapping for mapping in mappings}


def _declared_source_name(variable: DatasetVariable) -> str:
    return variable.source_field_name or variable.variable_id


def _duplicates(values: tuple[str, ...]) -> tuple[str, ...]:
    counts = Counter(values)
    duplicates: list[str] = []
    for value in values:
        if counts[value] > 1 and value and value not in duplicates:
            duplicates.append(value)
    return tuple(duplicates)
