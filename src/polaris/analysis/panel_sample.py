"""Panel sample construction with deterministic entity-time indexing and lags."""

from collections import Counter

from polaris.analysis.errors import DuplicatePanelKeyError, InvalidLagError
from polaris.analysis.models import (
    AnalysisFinding,
    AnalysisFindingCode,
    AnalysisSample,
    FindingSeverity,
    PanelLagOperation,
    RowExclusion,
)
from polaris.ingestion.models import DatasetIngestionResult, NormalizedRecord
from polaris.schemas.statistics import LagSpec


def build_panel_sample(
    ingestion_result: DatasetIngestionResult,
    *,
    variable_ids: tuple[str, ...],
    entity_variable_id: str,
    time_variable_id: str,
    lags: tuple[LagSpec, ...],
) -> tuple[AnalysisSample, tuple[PanelLagOperation, ...], tuple[AnalysisFinding, ...]]:
    _reject_duplicate_keys(
        ingestion_result.normalized_records, entity_variable_id, time_variable_id
    )
    records = sorted(
        ingestion_result.normalized_records,
        key=lambda record: (
            str(record.values.get(entity_variable_id)),
            _numeric_time(record.values.get(time_variable_id), record.row_number),
            record.row_number,
        ),
    )
    lag_values, lag_operations = _generate_lags(
        records,
        entity_variable_id=entity_variable_id,
        time_variable_id=time_variable_id,
        lags=lags,
    )
    model_variables = tuple(
        dict.fromkeys(
            (
                *variable_ids,
                *(operation.generated_variable_id for operation in lag_operations),
                entity_variable_id,
                time_variable_id,
            )
        )
    )
    rows: list[dict[str, int | float | str | bool]] = []
    included_rows: list[int] = []
    included_lines: list[int] = []
    exclusions: list[RowExclusion] = []

    for record in records:
        values = dict(record.values)
        values.update(lag_values.get(record.row_number, {}))
        missing = tuple(
            variable_id for variable_id in model_variables if values.get(variable_id) is None
        )
        if missing:
            exclusions.append(
                RowExclusion(
                    row_number=record.row_number,
                    source_line_number=record.source_line_number,
                    reason="panel complete-case analysis excluded row with missing required values",
                    variable_ids=missing,
                )
            )
            continue
        rows.append({variable_id: values[variable_id] for variable_id in model_variables})  # type: ignore[dict-item]
        included_rows.append(record.row_number)
        included_lines.append(record.source_line_number)

    findings: list[AnalysisFinding] = []
    if exclusions:
        findings.append(
            AnalysisFinding(
                severity=FindingSeverity.INFO,
                code=AnalysisFindingCode.EXCLUDED_MISSING_ROWS,
                message="panel complete-case analysis excluded rows with missing required values",
                variable_ids=model_variables,
                source_row_numbers=tuple(exclusion.row_number for exclusion in exclusions),
            )
        )
    if lag_operations:
        lost = tuple(
            row_number
            for operation in lag_operations
            for row_number in operation.excluded_row_numbers
        )
        if lost:
            findings.append(
                AnalysisFinding(
                    severity=FindingSeverity.INFO,
                    code=AnalysisFindingCode.LAG_EXCLUDED_ROWS,
                    message=(
                        "explicit panel lag construction excluded rows without valid prior periods"
                    ),
                    source_row_numbers=tuple(sorted(set(lost))),
                )
            )
    return (
        AnalysisSample(
            variable_ids=model_variables,
            rows=tuple(rows),
            included_row_numbers=tuple(included_rows),
            included_source_line_numbers=tuple(included_lines),
            exclusions=tuple(exclusions),
        ),
        lag_operations,
        tuple(findings),
    )


def lagged_variable_id(lag: LagSpec) -> str:
    if lag.generated_variable_id is not None:
        return lag.generated_variable_id
    return f"{lag.source_variable.variable_id}_lag{lag.lag_periods}"


def _reject_duplicate_keys(
    records: tuple[NormalizedRecord, ...],
    entity_variable_id: str,
    time_variable_id: str,
) -> None:
    keys = [
        (record.values.get(entity_variable_id), record.values.get(time_variable_id))
        for record in records
        if record.values.get(entity_variable_id) is not None
        and record.values.get(time_variable_id) is not None
    ]
    duplicates = [key for key, count in Counter(keys).items() if count > 1]
    if duplicates:
        raise DuplicatePanelKeyError(
            "panel analysis rejects duplicate entity-time rows: "
            + ", ".join(f"{entity}:{time}" for entity, time in duplicates[:5])
        )


def _generate_lags(
    records: list[NormalizedRecord],
    *,
    entity_variable_id: str,
    time_variable_id: str,
    lags: tuple[LagSpec, ...],
) -> tuple[dict[int, dict[str, int | float | str | bool]], tuple[PanelLagOperation, ...]]:
    generated: dict[int, dict[str, int | float | str | bool]] = {}
    operations: list[PanelLagOperation] = []
    by_entity: dict[str, list[NormalizedRecord]] = {}
    for record in records:
        entity = record.values.get(entity_variable_id)
        if entity is not None:
            by_entity.setdefault(str(entity), []).append(record)

    for lag in lags:
        source_id = lag.source_variable.variable_id
        generated_id = lagged_variable_id(lag)
        excluded: list[int] = []
        reasons: list[tuple[int, str]] = []
        for entity_records in by_entity.values():
            ordered = sorted(
                entity_records,
                key=lambda record: (
                    _numeric_time(record.values.get(time_variable_id), record.row_number),
                    record.row_number,
                ),
            )
            by_time = {
                _numeric_time(record.values.get(time_variable_id), record.row_number): record
                for record in ordered
            }
            for record in ordered:
                current_time = _numeric_time(record.values.get(time_variable_id), record.row_number)
                prior_time = current_time - lag.lag_periods
                prior = by_time.get(prior_time)
                if lag.require_consecutive_time and prior is None:
                    excluded.append(record.row_number)
                    reasons.append((record.row_number, "missing required consecutive prior period"))
                    continue
                if prior is None or prior.values.get(source_id) is None:
                    excluded.append(record.row_number)
                    reasons.append((record.row_number, "missing lagged source value"))
                    continue
                generated.setdefault(record.row_number, {})[generated_id] = prior.values[source_id]  # type: ignore[assignment]
        operations.append(
            PanelLagOperation(
                source_variable_id=source_id,
                generated_variable_id=generated_id,
                lag_periods=lag.lag_periods,
                require_consecutive_time=lag.require_consecutive_time,
                rows_lost=len(set(excluded)),
                excluded_row_numbers=tuple(sorted(set(excluded))),
                missing_lag_reasons=tuple(sorted(set(reasons))),
            )
        )
    return generated, tuple(operations)


def _numeric_time(value: object, row_number: int) -> int | float:
    if isinstance(value, bool) or value is None:
        raise InvalidLagError(f"panel time value is missing or invalid at row {row_number}")
    if isinstance(value, int | float):
        return value
    raise InvalidLagError(f"panel time value must be numeric at row {row_number}")
