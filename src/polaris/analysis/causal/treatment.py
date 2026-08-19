"""Treatment and event-time construction for explicit causal designs."""

from dataclasses import dataclass

from polaris.analysis.causal.errors import (
    InsufficientPostTreatmentDataError,
    InsufficientPreTreatmentDataError,
    InvalidTreatmentAssignmentError,
    InvalidTreatmentTimingError,
    MissingControlGroupError,
    UnsupportedStaggeredTreatmentError,
)
from polaris.analysis.causal.models import CausalSpecification
from polaris.analysis.models import AnalysisSample, RowExclusion
from polaris.ingestion.models import DatasetIngestionResult


@dataclass(frozen=True)
class TreatmentPanel:
    sample: AnalysisSample
    rows: tuple[dict[str, int | float | str | bool], ...]
    treated_entities: tuple[str, ...]
    control_entities: tuple[str, ...]
    treatment_start_period: float
    excluded_row_numbers: tuple[int, ...]


def build_treatment_panel(
    ingestion_result: DatasetIngestionResult,
    specification: CausalSpecification,
) -> TreatmentPanel:
    entity_id = specification.entity_variable.variable_id
    time_id = specification.time_variable.variable_id
    outcome_id = specification.outcome_variable.variable_id
    treatment_id = specification.treatment.treatment_variable.variable_id
    covariate_ids = tuple(item.variable_id for item in specification.covariates)
    timing_id = (
        specification.treatment.treatment_timing_variable.variable_id
        if specification.treatment.treatment_timing_variable is not None
        else None
    )
    timing_variables = (timing_id,) if timing_id else ()
    required = tuple(
        dict.fromkeys(
            (entity_id, time_id, outcome_id, treatment_id, *timing_variables, *covariate_ids)
        )
    )
    rows: list[dict[str, int | float | str | bool]] = []
    included_rows: list[int] = []
    included_lines: list[int] = []
    exclusions: list[RowExclusion] = []
    for record in sorted(
        ingestion_result.normalized_records,
        key=lambda item: (
            str(item.values.get(entity_id)),
            _numeric_time(item.values.get(time_id), item.row_number),
            item.row_number,
        ),
    ):
        missing = tuple(
            variable_id for variable_id in required if record.values.get(variable_id) is None
        )
        if missing:
            exclusions.append(
                RowExclusion(
                    row_number=record.row_number,
                    source_line_number=record.source_line_number,
                    reason=(
                        "causal complete-case analysis excluded row with missing required values"
                    ),
                    variable_ids=missing,
                )
            )
            continue
        row = {variable_id: record.values[variable_id] for variable_id in required}
        row["_source_row_number"] = record.row_number
        rows.append(row)  # type: ignore[arg-type]
        included_rows.append(record.row_number)
        included_lines.append(record.source_line_number)

    treated_entities, control_entities = _entity_groups(
        rows,
        entity_id=entity_id,
        treatment_id=treatment_id,
        treated_value=specification.treatment.treated_value,
        control_value=specification.treatment.control_value,
    )
    treatment_start = _treatment_start(
        rows,
        entity_id=entity_id,
        timing_id=timing_id,
        explicit_start=specification.treatment.treatment_start_period,
        treated_entities=set(treated_entities),
    )
    _validate_coverage(
        rows,
        specification,
        entity_id=entity_id,
        time_id=time_id,
        treated_entities=treated_entities,
        control_entities=control_entities,
        treatment_start=treatment_start,
    )
    model_variables = tuple(dict.fromkeys((*required, "_source_row_number")))
    sample = AnalysisSample(
        variable_ids=model_variables,
        rows=tuple(rows),
        included_row_numbers=tuple(included_rows),
        included_source_line_numbers=tuple(included_lines),
        exclusions=tuple(exclusions),
    )
    return TreatmentPanel(
        sample=sample,
        rows=tuple(rows),
        treated_entities=treated_entities,
        control_entities=control_entities,
        treatment_start_period=treatment_start,
        excluded_row_numbers=tuple(exclusion.row_number for exclusion in exclusions),
    )


def _entity_groups(
    rows: list[dict[str, int | float | str | bool]],
    *,
    entity_id: str,
    treatment_id: str,
    treated_value: object,
    control_value: object,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    values_by_entity: dict[str, set[object]] = {}
    for row in rows:
        values_by_entity.setdefault(str(row[entity_id]), set()).add(row[treatment_id])
    invalid = {
        entity: values
        for entity, values in values_by_entity.items()
        if not values <= {treated_value, control_value} or len(values) != 1
    }
    if invalid:
        raise InvalidTreatmentAssignmentError(
            "causal designs require a stable entity-level treated/control indicator"
        )
    treated = tuple(
        sorted(entity for entity, values in values_by_entity.items() if treated_value in values)
    )
    controls = tuple(
        sorted(entity for entity, values in values_by_entity.items() if control_value in values)
    )
    if not treated:
        raise InvalidTreatmentAssignmentError("no treated entities were identified")
    if not controls:
        raise MissingControlGroupError("no valid never-treated comparison entities were identified")
    return treated, controls


def _treatment_start(
    rows: list[dict[str, int | float | str | bool]],
    *,
    entity_id: str,
    timing_id: str | None,
    explicit_start: int | float | None,
    treated_entities: set[str],
) -> float:
    if timing_id is None:
        if explicit_start is None:
            raise InvalidTreatmentTimingError("missing treatment start period")
        return float(explicit_start)
    starts = {
        float(row[timing_id])
        for row in rows
        if str(row[entity_id]) in treated_entities and row.get(timing_id) is not None
    }
    if not starts:
        raise InvalidTreatmentTimingError("treated entities lack treatment timing values")
    if len(starts) > 1:
        raise UnsupportedStaggeredTreatmentError(
            "Phase 22 rejects staggered treatment timing for TWFE DiD/event-study estimators"
        )
    start = next(iter(starts))
    if explicit_start is not None and float(explicit_start) != start:
        raise InvalidTreatmentTimingError(
            "explicit treatment_start_period conflicts with timing variable"
        )
    return start


def _validate_coverage(
    rows: list[dict[str, int | float | str | bool]],
    specification: CausalSpecification,
    *,
    entity_id: str,
    time_id: str,
    treated_entities: tuple[str, ...],
    control_entities: tuple[str, ...],
    treatment_start: float,
) -> None:
    pre_start, pre_end = (float(value) for value in specification.pre_treatment_window)
    post_start, post_end = (float(value) for value in specification.post_treatment_window)
    if pre_end >= treatment_start:
        raise InvalidTreatmentTimingError("pre-treatment window must end before treatment starts")
    if post_start < treatment_start:
        raise InvalidTreatmentTimingError(
            "post-treatment window must start at or after treatment starts"
        )
    by_entity: dict[str, set[float]] = {}
    for row in rows:
        by_entity.setdefault(str(row[entity_id]), set()).add(float(row[time_id]))

    for entity in treated_entities:
        times = by_entity.get(entity, set())
        if not any(pre_start <= time <= pre_end for time in times):
            raise InsufficientPreTreatmentDataError(
                f'treated entity "{entity}" lacks required pre-treatment observations'
            )
        if not any(post_start <= time <= post_end for time in times):
            raise InsufficientPostTreatmentDataError(
                f'treated entity "{entity}" lacks required post-treatment observations'
            )
    valid_controls = 0
    for entity in control_entities:
        times = by_entity.get(entity, set())
        if any(pre_start <= time <= pre_end for time in times) and any(
            post_start <= time <= post_end for time in times
        ):
            valid_controls += 1
    if valid_controls == 0:
        raise MissingControlGroupError("controls lack observations over required pre/post periods")


def _numeric_time(value: object, row_number: int) -> float:
    if isinstance(value, bool) or value is None:
        raise InvalidTreatmentTimingError(
            f"causal time value is missing or invalid at row {row_number}"
        )
    if isinstance(value, int | float):
        return float(value)
    raise InvalidTreatmentTimingError(f"causal time value must be numeric at row {row_number}")
