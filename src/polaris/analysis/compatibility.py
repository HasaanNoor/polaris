"""Pre-execution compatibility validation for Phase 4 methods."""

from collections import Counter

from polaris.analysis.errors import (
    AnalysisCompatibilityError,
    InsufficientSampleError,
    UnsupportedAnalysisMethodError,
    VariableNotFoundError,
    VariableTypeError,
)
from polaris.analysis.models import AnalysisFinding, AnalysisFindingCode, FindingSeverity
from polaris.analysis.sample import build_analysis_sample
from polaris.ingestion.models import DatasetIngestionResult
from polaris.schemas.common import (
    CausalIdentificationLevel,
    DataType,
    StatisticalAnalysisType,
    StatisticalModelFamily,
    StatisticalProcedure,
)
from polaris.schemas.dataset import DatasetVariable
from polaris.schemas.statistics import StatisticalSpecification

NUMERIC_TYPES = {DataType.INTEGER, DataType.FLOAT}


def resolve_procedure(specification: StatisticalSpecification) -> StatisticalProcedure:
    if specification.procedure is not None:
        return specification.procedure
    if specification.analysis_type is StatisticalAnalysisType.DESCRIPTIVE:
        return StatisticalProcedure.DESCRIPTIVE_STATISTICS
    if (
        specification.analysis_type is StatisticalAnalysisType.REGRESSION
        and specification.model_family is StatisticalModelFamily.LINEAR
    ):
        return StatisticalProcedure.ORDINARY_LEAST_SQUARES
    raise UnsupportedAnalysisMethodError(
        "statistical specification must explicitly name a supported procedure",
        method=specification.analysis_type.value,
    )


def required_variables(specification: StatisticalSpecification) -> tuple[str, ...]:
    values = [
        specification.outcome_variable.variable_id,
        *(variable.variable_id for variable in specification.exposure_variables),
        *(variable.variable_id for variable in specification.covariates),
    ]
    return tuple(dict.fromkeys(values))


def validate_compatibility(
    ingestion_result: DatasetIngestionResult,
    specification: StatisticalSpecification,
    procedure: StatisticalProcedure,
) -> tuple[tuple[str, ...], tuple[AnalysisFinding, ...]]:
    variables = {
        variable.variable_id: variable for variable in ingestion_result.dataset_manifest.variables
    }
    requested = required_variables(specification)
    findings: list[AnalysisFinding] = []

    _reject_unsupported_options(specification)
    _reject_causal_claims(specification, procedure, findings)

    for variable_id in requested:
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

    if procedure is StatisticalProcedure.DESCRIPTIVE_STATISTICS:
        return requested, tuple(findings)
    if procedure in {
        StatisticalProcedure.PEARSON_CORRELATION,
        StatisticalProcedure.SPEARMAN_CORRELATION,
    }:
        _validate_correlation(specification, variables, procedure)
    elif procedure is StatisticalProcedure.ORDINARY_LEAST_SQUARES:
        _validate_ols(specification, variables, procedure)
    elif procedure is StatisticalProcedure.BINARY_LOGISTIC_REGRESSION:
        raise UnsupportedAnalysisMethodError(
            "binary logistic regression is deferred in Phase 4",
            dataset_id=ingestion_result.dataset_manifest.dataset_id,
            method=procedure.value,
        )
    else:
        raise UnsupportedAnalysisMethodError(
            f'unsupported analysis procedure "{procedure.value}"',
            dataset_id=ingestion_result.dataset_manifest.dataset_id,
            method=procedure.value,
        )

    sample, _ = build_analysis_sample(ingestion_result, requested)
    if (
        procedure
        in {
            StatisticalProcedure.PEARSON_CORRELATION,
            StatisticalProcedure.SPEARMAN_CORRELATION,
        }
        and sample.sample_size < 2
    ):
        raise InsufficientSampleError(
            "correlation requires at least two complete observations",
            dataset_id=ingestion_result.dataset_manifest.dataset_id,
            method=procedure.value,
            sample_size=sample.sample_size,
        )
    if procedure is StatisticalProcedure.ORDINARY_LEAST_SQUARES:
        predictor_count = len(_predictor_ids(specification))
        min_rows = predictor_count + 3
        if sample.sample_size <= min_rows:
            raise InsufficientSampleError(
                "OLS regression requires at least three residual degrees of freedom",
                dataset_id=ingestion_result.dataset_manifest.dataset_id,
                method=procedure.value,
                sample_size=sample.sample_size,
            )
    findings.extend(_variable_structure_findings(ingestion_result, requested, procedure))
    return requested, tuple(findings)


def _validate_correlation(
    specification: StatisticalSpecification,
    variables: dict[str, DatasetVariable],
    procedure: StatisticalProcedure,
) -> None:
    if len(required_variables(specification)) < 2:
        raise AnalysisCompatibilityError("correlation requires at least two variables")
    for variable_id in required_variables(specification):
        _require_numeric(variables[variable_id], procedure)


def _validate_ols(
    specification: StatisticalSpecification,
    variables: dict[str, DatasetVariable],
    procedure: StatisticalProcedure,
) -> None:
    outcome_id = specification.outcome_variable.variable_id
    predictor_ids = _predictor_ids(specification)
    if not predictor_ids:
        raise AnalysisCompatibilityError("OLS regression requires at least one predictor")
    counts = Counter(predictor_ids)
    duplicate_predictors = tuple(variable_id for variable_id, count in counts.items() if count > 1)
    if duplicate_predictors:
        raise AnalysisCompatibilityError(
            "OLS regression rejects duplicate predictors: " + ", ".join(duplicate_predictors)
        )
    if outcome_id in predictor_ids:
        raise AnalysisCompatibilityError("dependent variable cannot also be a predictor")
    _require_numeric(variables[outcome_id], procedure)
    for variable_id in predictor_ids:
        _require_numeric(variables[variable_id], procedure)


def _require_numeric(variable: DatasetVariable, procedure: StatisticalProcedure) -> None:
    if variable.data_type not in NUMERIC_TYPES:
        raise VariableTypeError(
            f'variable "{variable.variable_id}" has type "{variable.data_type.value}", not numeric',
            method=procedure.value,
            variable_id=variable.variable_id,
        )


def _predictor_ids(specification: StatisticalSpecification) -> tuple[str, ...]:
    return tuple(
        variable.variable_id
        for variable in (*specification.exposure_variables, *specification.covariates)
    )


def _reject_unsupported_options(specification: StatisticalSpecification) -> None:
    unsupported: list[str] = []
    if specification.grouping_variables:
        unsupported.append("grouping_variables")
    if specification.fixed_effects:
        unsupported.append("fixed_effects")
    if specification.weighting is not None and specification.weighting.weight_variable is not None:
        unsupported.append("weighting")
    if specification.time_variable is not None:
        unsupported.append("time_variable")
    if specification.transformations:
        unsupported.append("transformations")
    if specification.standard_error_strategy is not None:
        unsupported.append("standard_error_strategy")
    if unsupported:
        raise UnsupportedAnalysisMethodError(
            "Phase 4 does not support specification options: " + ", ".join(unsupported)
        )


def _reject_causal_claims(
    specification: StatisticalSpecification,
    procedure: StatisticalProcedure,
    findings: list[AnalysisFinding],
) -> None:
    allowed = {
        CausalIdentificationLevel.NOT_CAUSAL,
        CausalIdentificationLevel.DESCRIPTIVE_ONLY,
        CausalIdentificationLevel.ASSOCIATIONAL,
        CausalIdentificationLevel.PREDICTIVE_ONLY,
    }
    if specification.causal_identification_claim_level not in allowed:
        findings.append(
            AnalysisFinding(
                severity=FindingSeverity.WARNING,
                code=AnalysisFindingCode.CAUSAL_INTERPRETATION_UNSUPPORTED,
                message="Phase 4 reports statistical facts only and does not support causal claims",
                method=procedure.value,
            )
        )


def _variable_structure_findings(
    ingestion_result: DatasetIngestionResult,
    variable_ids: tuple[str, ...],
    procedure: StatisticalProcedure,
) -> tuple[AnalysisFinding, ...]:
    findings: list[AnalysisFinding] = []
    for variable_id in variable_ids:
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
