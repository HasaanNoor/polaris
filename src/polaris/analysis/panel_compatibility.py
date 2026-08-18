"""Compatibility validation for explicit panel specifications."""

from collections import Counter

from polaris.analysis.compatibility import NUMERIC_TYPES, _require_numeric
from polaris.analysis.errors import (
    AnalysisCompatibilityError,
    InsufficientPanelDataError,
    PanelSpecificationError,
    UnsupportedAnalysisMethodError,
    VariableNotFoundError,
    VariableTypeError,
)
from polaris.analysis.models import AnalysisFinding, AnalysisFindingCode, FindingSeverity
from polaris.ingestion.models import DatasetIngestionResult
from polaris.schemas.common import DataType, StatisticalProcedure
from polaris.schemas.dataset import DatasetVariable
from polaris.schemas.statistics import StatisticalSpecification

PANEL_PROCEDURES = {
    StatisticalProcedure.PANEL_ENTITY_FE,
    StatisticalProcedure.PANEL_TWO_WAY_FE,
    StatisticalProcedure.FIRST_DIFFERENCE,
}


def is_panel_procedure(procedure: StatisticalProcedure) -> bool:
    return procedure in PANEL_PROCEDURES


def panel_required_variables(specification: StatisticalSpecification) -> tuple[str, ...]:
    entity = _entity_id(specification)
    time = _time_id(specification)
    predictors = _predictor_ids(specification)
    lag_sources = tuple(lag.source_variable.variable_id for lag in specification.lags)
    lagged = tuple(
        lag.generated_variable_id or f"{lag.source_variable.variable_id}_lag{lag.lag_periods}"
        for lag in specification.lags
    )
    return tuple(
        dict.fromkeys(
            (
                specification.outcome_variable.variable_id,
                *predictors,
                *lag_sources,
                *lagged,
                entity,
                time,
            )
        )
    )


def validate_panel_compatibility(
    ingestion_result: DatasetIngestionResult,
    specification: StatisticalSpecification,
    procedure: StatisticalProcedure,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[AnalysisFinding, ...]]:
    if procedure not in PANEL_PROCEDURES:
        raise UnsupportedAnalysisMethodError(f'unsupported panel procedure "{procedure.value}"')
    variables = {
        variable.variable_id: variable for variable in ingestion_result.dataset_manifest.variables
    }
    entity_id = _entity_id(specification)
    time_id = _time_id(specification)
    base_predictors = _predictor_ids(specification)
    lagged_predictors = tuple(
        lag.generated_variable_id or f"{lag.source_variable.variable_id}_lag{lag.lag_periods}"
        for lag in specification.lags
    )
    model_predictors = tuple(dict.fromkeys((*base_predictors, *lagged_predictors)))
    if not model_predictors:
        raise AnalysisCompatibilityError("panel regression requires at least one predictor")
    if specification.outcome_variable.variable_id in model_predictors:
        raise AnalysisCompatibilityError("dependent variable cannot also be a predictor")
    if procedure is StatisticalProcedure.PANEL_ENTITY_FE and not _has_fixed_effect(
        specification, entity_id
    ):
        raise PanelSpecificationError("entity fixed effects must be declared for panel_entity_fe")
    if procedure is StatisticalProcedure.PANEL_TWO_WAY_FE and (
        not _has_fixed_effect(specification, entity_id)
        or not _has_fixed_effect(specification, time_id)
    ):
        raise PanelSpecificationError(
            "entity and time fixed effects must be declared for panel_two_way_fe"
        )
    if specification.standard_error_strategy is None:
        raise PanelSpecificationError(
            "panel regression requires explicit clustered standard errors"
        )
    if not specification.standard_error_strategy.cluster_variables:
        raise PanelSpecificationError("panel regression requires a cluster variable")
    cluster_ids = tuple(
        variable.variable_id for variable in specification.standard_error_strategy.cluster_variables
    )
    if cluster_ids != (entity_id,):
        raise PanelSpecificationError("Phase 21 supports clustering by entity only")

    requested_manifest_variables = tuple(
        dict.fromkeys(
            (
                specification.outcome_variable.variable_id,
                *base_predictors,
                *(lag.source_variable.variable_id for lag in specification.lags),
                entity_id,
                time_id,
                *cluster_ids,
            )
        )
    )
    for variable_id in requested_manifest_variables:
        if variable_id not in variables:
            raise VariableNotFoundError(
                f'requested variable "{variable_id}" is not declared by the dataset manifest',
                dataset_id=ingestion_result.dataset_manifest.dataset_id,
                method=procedure.value,
                variable_id=variable_id,
            )
        if any(variable_id not in record.values for record in ingestion_result.normalized_records):
            raise VariableNotFoundError(
                f'requested variable "{variable_id}" is absent from normalized records',
                dataset_id=ingestion_result.dataset_manifest.dataset_id,
                method=procedure.value,
                variable_id=variable_id,
            )
    _require_numeric(variables[specification.outcome_variable.variable_id], procedure)
    for variable_id in (
        *base_predictors,
        *(lag.source_variable.variable_id for lag in specification.lags),
    ):
        _require_numeric(variables[variable_id], procedure)
    _require_time(variables[time_id], procedure)
    _reject_duplicate_predictors(model_predictors)
    findings = list(
        _panel_structure_findings(ingestion_result, requested_manifest_variables, procedure)
    )
    _require_repeated_observations(ingestion_result, entity_id, time_id, procedure)
    return panel_required_variables(specification), model_predictors, tuple(findings)


def _entity_id(specification: StatisticalSpecification) -> str:
    if specification.entity_variable is None:
        raise PanelSpecificationError("panel analysis requires entity_variable")
    return specification.entity_variable.variable_id


def _time_id(specification: StatisticalSpecification) -> str:
    if specification.time_variable is None:
        raise PanelSpecificationError("panel analysis requires time_variable")
    return specification.time_variable.variable_id


def _predictor_ids(specification: StatisticalSpecification) -> tuple[str, ...]:
    return tuple(
        variable.variable_id
        for variable in (*specification.exposure_variables, *specification.covariates)
    )


def _has_fixed_effect(specification: StatisticalSpecification, variable_id: str) -> bool:
    return variable_id in {variable.variable_id for variable in specification.fixed_effects}


def _require_time(variable: DatasetVariable, procedure: StatisticalProcedure) -> None:
    if variable.data_type not in {DataType.INTEGER, DataType.FLOAT}:
        raise VariableTypeError(
            f'panel time variable "{variable.variable_id}" must be numeric',
            method=procedure.value,
            variable_id=variable.variable_id,
        )


def _reject_duplicate_predictors(predictor_ids: tuple[str, ...]) -> None:
    counts = Counter(predictor_ids)
    duplicates = tuple(variable_id for variable_id, count in counts.items() if count > 1)
    if duplicates:
        raise AnalysisCompatibilityError(
            "panel regression rejects duplicate predictors: " + ", ".join(duplicates)
        )


def _require_repeated_observations(
    ingestion_result: DatasetIngestionResult,
    entity_id: str,
    time_id: str,
    procedure: StatisticalProcedure,
) -> None:
    rows = [
        record
        for record in ingestion_result.normalized_records
        if record.values.get(entity_id) is not None and record.values.get(time_id) is not None
    ]
    counts = Counter(str(record.values[entity_id]) for record in rows)
    repeated = [entity for entity, count in counts.items() if count >= 2]
    if len(repeated) < 2:
        raise InsufficientPanelDataError(
            "panel analysis requires repeated observations for at least two entities",
            dataset_id=ingestion_result.dataset_manifest.dataset_id,
            method=procedure.value,
            sample_size=len(rows),
        )


def _panel_structure_findings(
    ingestion_result: DatasetIngestionResult,
    variable_ids: tuple[str, ...],
    procedure: StatisticalProcedure,
) -> tuple[AnalysisFinding, ...]:
    findings: list[AnalysisFinding] = []
    for variable_id in variable_ids:
        variable = next(
            item
            for item in ingestion_result.dataset_manifest.variables
            if item.variable_id == variable_id
        )
        if variable.data_type not in NUMERIC_TYPES:
            continue
        values = tuple(
            record.values.get(variable_id) for record in ingestion_result.normalized_records
        )
        non_null = tuple(value for value in values if value is not None)
        if not non_null:
            findings.append(
                AnalysisFinding(
                    severity=FindingSeverity.WARNING,
                    code=AnalysisFindingCode.ALL_NULL_VARIABLE,
                    message=f'variable "{variable_id}" has no non-missing accepted values',
                    variable_ids=(variable_id,),
                    method=procedure.value,
                )
            )
        elif len(set(non_null)) == 1:
            findings.append(
                AnalysisFinding(
                    severity=FindingSeverity.WARNING,
                    code=AnalysisFindingCode.CONSTANT_VARIABLE,
                    message=f'variable "{variable_id}" is constant in accepted records',
                    variable_ids=(variable_id,),
                    method=procedure.value,
                )
            )
    return tuple(findings)
