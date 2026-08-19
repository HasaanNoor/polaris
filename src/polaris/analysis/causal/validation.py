"""Deterministic validation for explicit causal specifications."""

from polaris.analysis.causal.errors import CausalSpecificationError, InvalidEventWindowError
from polaris.analysis.causal.models import CausalMethod, CausalSpecification
from polaris.analysis.compatibility import _require_numeric
from polaris.ingestion.models import DatasetIngestionResult
from polaris.schemas.common import DataType, StatisticalProcedure


def validate_causal_compatibility(
    ingestion_result: DatasetIngestionResult,
    specification: CausalSpecification,
) -> tuple[str, ...]:
    variables = {
        variable.variable_id: variable for variable in ingestion_result.dataset_manifest.variables
    }
    required = tuple(
        dict.fromkeys(
            (
                specification.entity_variable.variable_id,
                specification.time_variable.variable_id,
                specification.outcome_variable.variable_id,
                specification.treatment.treatment_variable.variable_id,
                *(
                    (specification.treatment.treatment_timing_variable.variable_id,)
                    if specification.treatment.treatment_timing_variable is not None
                    else ()
                ),
                *(item.variable_id for item in specification.covariates),
            )
        )
    )
    for variable_id in required:
        if variable_id not in variables:
            raise CausalSpecificationError(
                f'requested causal variable "{variable_id}" is not declared by the manifest'
            )
        if any(variable_id not in record.values for record in ingestion_result.normalized_records):
            raise CausalSpecificationError(
                f'requested causal variable "{variable_id}" is absent from normalized records'
            )
    _require_numeric(
        variables[specification.outcome_variable.variable_id],
        StatisticalProcedure.ORDINARY_LEAST_SQUARES,
    )
    if variables[specification.time_variable.variable_id].data_type not in {
        DataType.INTEGER,
        DataType.FLOAT,
    }:
        raise CausalSpecificationError("causal time variable must be numeric")
    for covariate in specification.covariates:
        _require_numeric(
            variables[covariate.variable_id], StatisticalProcedure.ORDINARY_LEAST_SQUARES
        )
    if (
        specification.method is CausalMethod.EVENT_STUDY
        and specification.event_study is not None
        and specification.event_study.reference_event_time >= 0
    ):
        raise InvalidEventWindowError("event-study reference period should be pre-treatment")
    return required
