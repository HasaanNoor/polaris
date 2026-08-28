"""Specification transformations for explicit causal robustness variants."""

from __future__ import annotations

from dataclasses import dataclass

from polaris.analysis.causal.models import (
    CausalMethod,
    CausalSpecification,
    EventStudyConfig,
)
from polaris.analysis.causal.models import TreatmentAssignment as CausalTreatmentAssignment
from polaris.analysis.robustness.errors import (
    IncompatibleVariantError,
    InvalidPlaceboSpecificationError,
)
from polaris.analysis.robustness.models import RobustnessVariant, RobustnessVariantType
from polaris.ingestion.models import DatasetIngestionResult, NormalizedRecord


@dataclass(frozen=True)
class VariantExecutionInput:
    specification: CausalSpecification
    ingestion_result: DatasetIngestionResult
    excluded_entities: tuple[str, ...]


def apply_variant(
    *,
    baseline: CausalSpecification,
    ingestion_result: DatasetIngestionResult,
    variant: RobustnessVariant,
) -> VariantExecutionInput:
    """Build the causal request inputs for one explicit variant."""

    if variant.variant_type is RobustnessVariantType.ALTERNATIVE_TIME_WINDOW:
        return VariantExecutionInput(
            specification=baseline.model_copy(
                update={
                    "specification_id": variant.variant_id,
                    "pre_treatment_window": variant.pre_treatment_window,
                    "post_treatment_window": variant.post_treatment_window,
                }
            ),
            ingestion_result=ingestion_result,
            excluded_entities=(),
        )
    if variant.variant_type is RobustnessVariantType.COVARIATE_SET:
        return VariantExecutionInput(
            specification=baseline.model_copy(
                update={"specification_id": variant.variant_id, "covariates": variant.covariates}
            ),
            ingestion_result=ingestion_result,
            excluded_entities=(),
        )
    if variant.variant_type is RobustnessVariantType.CONFIDENCE_LEVEL:
        return VariantExecutionInput(
            specification=baseline.model_copy(
                update={
                    "specification_id": variant.variant_id,
                    "confidence_level": variant.confidence_level,
                }
            ),
            ingestion_result=ingestion_result,
            excluded_entities=(),
        )
    if variant.variant_type is RobustnessVariantType.TREATMENT_TIMING:
        return VariantExecutionInput(
            specification=_with_treatment_start(
                baseline,
                variant.variant_id,
                variant.treatment_start_period,
            ),
            ingestion_result=ingestion_result,
            excluded_entities=(),
        )
    if variant.variant_type is RobustnessVariantType.EVENT_STUDY_WINDOW:
        if baseline.method is not CausalMethod.EVENT_STUDY:
            raise IncompatibleVariantError(
                "event-study robustness requires an event-study baseline"
            )
        low, high = variant.event_study_window or (0, 0)
        return VariantExecutionInput(
            specification=baseline.model_copy(
                update={
                    "specification_id": variant.variant_id,
                    "event_study": EventStudyConfig(
                        min_event_time=low,
                        max_event_time=high,
                        reference_event_time=variant.event_study_reference_period,
                    ),
                }
            ),
            ingestion_result=ingestion_result,
            excluded_entities=(),
        )
    if variant.variant_type is RobustnessVariantType.ALTERNATIVE_CONTROL_GROUP:
        return _control_group_input(
            baseline=baseline,
            ingestion_result=ingestion_result,
            variant=variant,
            controls=variant.control_entities or (),
        )
    if variant.variant_type is RobustnessVariantType.LEAVE_ONE_TREATED_ENTITY_OUT:
        return _leave_one_out_input(
            baseline=baseline,
            ingestion_result=ingestion_result,
            variant=variant,
            omitted_role="treated",
        )
    if variant.variant_type is RobustnessVariantType.LEAVE_ONE_CONTROL_ENTITY_OUT:
        return _leave_one_out_input(
            baseline=baseline,
            ingestion_result=ingestion_result,
            variant=variant,
            omitted_role="control",
        )
    if variant.variant_type is RobustnessVariantType.PLACEBO_TIMING:
        placebo = variant.placebo_treatment_start_period
        if placebo is None or placebo >= baseline.treatment.treatment_start_period:
            raise InvalidPlaceboSpecificationError(
                "placebo treatment timing must be explicit and pre-treatment"
            )
        updates = {"specification_id": variant.variant_id}
        if variant.pre_treatment_window is not None:
            updates["pre_treatment_window"] = variant.pre_treatment_window
        if variant.post_treatment_window is not None:
            updates["post_treatment_window"] = variant.post_treatment_window
        return VariantExecutionInput(
            specification=_with_treatment_start(
                baseline.model_copy(update=updates), variant.variant_id, placebo
            ),
            ingestion_result=ingestion_result,
            excluded_entities=(),
        )
    if variant.variant_type is RobustnessVariantType.PLACEBO_ASSIGNMENT:
        return _placebo_assignment_input(
            baseline=baseline,
            ingestion_result=ingestion_result,
            variant=variant,
        )
    raise IncompatibleVariantError(f"unsupported robustness variant type: {variant.variant_type}")


def _with_treatment_start(
    baseline: CausalSpecification,
    variant_id: str,
    treatment_start: int | float | None,
) -> CausalSpecification:
    payload = baseline.treatment.model_dump(mode="python")
    payload.update(
        {
            "treatment_start_period": treatment_start,
            "treatment_timing_variable": None,
            "treatment_source": (
                f"{baseline.treatment.treatment_source};robustness_variant:{variant_id}"
            ),
        }
    )
    treatment = CausalTreatmentAssignment(**payload)
    return baseline.model_copy(update={"specification_id": variant_id, "treatment": treatment})


def _control_group_input(
    *,
    baseline: CausalSpecification,
    ingestion_result: DatasetIngestionResult,
    variant: RobustnessVariant,
    controls: tuple[str, ...],
) -> VariantExecutionInput:
    entity_id = baseline.entity_variable.variable_id
    treatment_id = baseline.treatment.treatment_variable.variable_id
    treated = _entities_by_treatment(
        ingestion_result,
        entity_id=entity_id,
        treatment_id=treatment_id,
        value=baseline.treatment.treated_value,
    )
    keep = set(treated) | set(controls)
    excluded = tuple(sorted(_all_entities(ingestion_result, entity_id) - keep))
    return VariantExecutionInput(
        specification=baseline.model_copy(
            update={
                "specification_id": variant.variant_id,
                "comparison_group_description": ", ".join(sorted(controls)),
            }
        ),
        ingestion_result=_filter_entities(ingestion_result, entity_id, keep),
        excluded_entities=excluded,
    )


def _leave_one_out_input(
    *,
    baseline: CausalSpecification,
    ingestion_result: DatasetIngestionResult,
    variant: RobustnessVariant,
    omitted_role: str,
) -> VariantExecutionInput:
    entity_id = baseline.entity_variable.variable_id
    omitted = variant.omitted_entity
    if omitted is None:
        raise IncompatibleVariantError("leave-one-out variant requires an omitted entity")
    keep = _all_entities(ingestion_result, entity_id) - {omitted}
    return VariantExecutionInput(
        specification=baseline.model_copy(update={"specification_id": variant.variant_id}),
        ingestion_result=_filter_entities(ingestion_result, entity_id, keep),
        excluded_entities=(omitted,),
    )


def _placebo_assignment_input(
    *,
    baseline: CausalSpecification,
    ingestion_result: DatasetIngestionResult,
    variant: RobustnessVariant,
) -> VariantExecutionInput:
    entity_id = baseline.entity_variable.variable_id
    treatment_id = baseline.treatment.treatment_variable.variable_id
    placebo_entities = set(variant.placebo_treated_entities or ())
    if not placebo_entities:
        raise InvalidPlaceboSpecificationError("placebo assignment requires explicit entities")
    records: list[NormalizedRecord] = []
    for record in ingestion_result.normalized_records:
        values = dict(record.values)
        values[treatment_id] = (
            baseline.treatment.treated_value
            if str(values[entity_id]) in placebo_entities
            else baseline.treatment.control_value
        )
        records.append(record.model_copy(update={"values": values}))
    return VariantExecutionInput(
        specification=baseline.model_copy(
            update={
                "specification_id": variant.variant_id,
                "treated_group_description": ", ".join(sorted(placebo_entities)),
                "comparison_group_description": "baseline controls plus original treated entities",
            }
        ),
        ingestion_result=ingestion_result.model_copy(update={"normalized_records": tuple(records)}),
        excluded_entities=(),
    )


def _filter_entities(
    ingestion_result: DatasetIngestionResult, entity_id: str, keep: set[str]
) -> DatasetIngestionResult:
    records = tuple(
        record
        for record in ingestion_result.normalized_records
        if str(record.values[entity_id]) in keep
    )
    return ingestion_result.model_copy(update={"normalized_records": records})


def _entities_by_treatment(
    ingestion_result: DatasetIngestionResult,
    *,
    entity_id: str,
    treatment_id: str,
    value: object,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(record.values[entity_id])
                for record in ingestion_result.normalized_records
                if record.values[treatment_id] == value
            }
        )
    )


def _all_entities(ingestion_result: DatasetIngestionResult, entity_id: str) -> set[str]:
    return {str(record.values[entity_id]) for record in ingestion_result.normalized_records}
