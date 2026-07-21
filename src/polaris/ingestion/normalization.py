"""Value coercion and normalized record construction."""

import math
import re
from datetime import date, datetime

from polaris.ingestion.models import (
    ColumnMapping,
    IngestionConfiguration,
    LoadedTabularFile,
    NormalizedRecord,
    NormalizedValue,
    ValidationFinding,
    ValidationFindingCode,
    ValidationSeverity,
)
from polaris.schemas.common import DataType
from polaris.schemas.dataset import DatasetManifest, DatasetVariable

_INTEGER_PATTERN = re.compile(r"^[+-]?\d+$")


def normalize_rows(
    manifest: DatasetManifest,
    loaded_file: LoadedTabularFile,
    mappings: tuple[ColumnMapping, ...],
    configuration: IngestionConfiguration,
) -> tuple[tuple[NormalizedRecord, ...], tuple[ValidationFinding, ...]]:
    """Normalize mapped source values and reject rows with invalid typed values."""

    variables = {variable.variable_id: variable for variable in manifest.variables}
    normalized_records: list[NormalizedRecord] = []
    findings: list[ValidationFinding] = []
    manifest_null_tokens = {
        variable.variable_id: tuple(variable.missing_value_representation)
        for variable in manifest.variables
    }

    for row in loaded_file.rows:
        values: dict[str, NormalizedValue] = {}
        source_map: dict[str, str] = {}
        row_findings: list[ValidationFinding] = []

        for mapping in mappings:
            variable = variables[mapping.variable_id]
            raw_value = row.values[mapping.source_index]
            normalized_value, finding = normalize_value(
                raw_value=raw_value,
                variable=variable,
                configuration=configuration,
                source_path=loaded_file.source_path,
                row_number=row.row_number,
                source_column=mapping.source_column,
                null_tokens=manifest_null_tokens[mapping.variable_id],
            )
            values[mapping.variable_id] = normalized_value
            source_map[mapping.variable_id] = mapping.source_column
            if finding is not None:
                row_findings.append(finding)

        findings.extend(row_findings)
        if any(finding.severity is ValidationSeverity.ERROR for finding in row_findings):
            continue

        normalized_records.append(
            NormalizedRecord(
                row_number=row.row_number,
                source_line_number=row.line_number,
                values=values,
                source_columns=source_map,
            )
        )

    return tuple(normalized_records), tuple(findings)


def normalize_value(
    *,
    raw_value: str,
    variable: DatasetVariable,
    configuration: IngestionConfiguration,
    source_path: str,
    row_number: int,
    source_column: str,
    null_tokens: tuple[str, ...],
) -> tuple[NormalizedValue, ValidationFinding | None]:
    """Normalize one raw CSV value according to a manifest variable."""

    stripped = raw_value.strip()
    if stripped in set(configuration.null_value_tokens) | set(null_tokens):
        return None, None

    if variable.data_type in {DataType.STRING, DataType.CATEGORICAL}:
        return stripped, None

    if not configuration.allow_type_coercion:
        return (
            None,
            _invalid_value_finding(
                variable=variable,
                source_path=source_path,
                row_number=row_number,
                source_column=source_column,
                raw_value=raw_value,
                expected=variable.data_type.value,
            ),
        )

    try:
        match variable.data_type:
            case DataType.INTEGER:
                return _coerce_integer(stripped), None
            case DataType.FLOAT:
                return _coerce_float(stripped), None
            case DataType.BOOLEAN:
                return _coerce_boolean(stripped), None
            case DataType.DATE:
                return date.fromisoformat(stripped), None
            case DataType.DATETIME:
                return datetime.fromisoformat(stripped), None
    except ValueError:
        return (
            None,
            _invalid_value_finding(
                variable=variable,
                source_path=source_path,
                row_number=row_number,
                source_column=source_column,
                raw_value=raw_value,
                expected=variable.data_type.value,
            ),
        )

    return (
        None,
        _invalid_value_finding(
            variable=variable,
            source_path=source_path,
            row_number=row_number,
            source_column=source_column,
            raw_value=raw_value,
            expected=variable.data_type.value,
        ),
    )


def _coerce_integer(value: str) -> int:
    if not _INTEGER_PATTERN.fullmatch(value):
        raise ValueError("invalid integer")
    return int(value)


def _coerce_float(value: str) -> float:
    if "," in value:
        raise ValueError("locale-dependent numeric parsing is unsupported")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("non-finite floats are unsupported")
    return result


def _coerce_boolean(value: str) -> bool:
    normalized = value.casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError("invalid boolean")


def _invalid_value_finding(
    *,
    variable: DatasetVariable,
    source_path: str,
    row_number: int,
    source_column: str,
    raw_value: str,
    expected: str,
) -> ValidationFinding:
    return ValidationFinding(
        severity=ValidationSeverity.ERROR,
        code=ValidationFindingCode.INVALID_VALUE_TYPE,
        message=f'value for variable "{variable.variable_id}" is not a valid {expected}',
        source_path=source_path,
        row_number=row_number,
        source_column=source_column,
        variable_id=variable.variable_id,
        raw_value=raw_value,
    )
