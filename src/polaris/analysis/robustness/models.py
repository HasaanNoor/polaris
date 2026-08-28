"""Typed contracts for Phase 24 causal robustness artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator, model_validator

from polaris import __version__
from polaris.analysis.causal.models import (
    CausalAnalysisResult,
    CausalEstimand,
    CausalMethod,
    CausalSpecification,
)
from polaris.causal_studies.models import DesignReadinessAssessment
from polaris.schemas.common import (
    AwareDatetime,
    DatasetId,
    FrozenPolarisBaseModel,
    NonEmptyStr,
    SchemaVersion,
    VariableId,
    VariableReference,
)

ROBUSTNESS_SCHEMA_VERSION = "1.0.0"
ROBUSTNESS_RULESET_VERSION = "causal_robustness_phase24_v1"


class RobustnessStrictness(StrEnum):
    STRICT = "strict"
    REVIEWED = "reviewed"


class RobustnessVariantType(StrEnum):
    ALTERNATIVE_TIME_WINDOW = "alternative_time_window"
    ALTERNATIVE_CONTROL_GROUP = "alternative_control_group"
    COVARIATE_SET = "covariate_set"
    LEAVE_ONE_TREATED_ENTITY_OUT = "leave_one_treated_entity_out"
    LEAVE_ONE_CONTROL_ENTITY_OUT = "leave_one_control_entity_out"
    PLACEBO_TIMING = "placebo_timing"
    PLACEBO_ASSIGNMENT = "placebo_assignment"
    EVENT_STUDY_WINDOW = "event_study_window"
    CONFIDENCE_LEVEL = "confidence_level"
    TREATMENT_TIMING = "treatment_timing"


class RobustnessEvidenceStatus(StrEnum):
    ROBUSTNESS_CONSISTENT = "robustness_consistent"
    ROBUSTNESS_MIXED = "robustness_mixed"
    ROBUSTNESS_SENSITIVE = "robustness_sensitive"
    ROBUSTNESS_INSUFFICIENT = "robustness_insufficient"


class ParallelTrendRobustnessStatus(StrEnum):
    CONSISTENT_CONCERN = "consistent_concern"
    SOME_CONCERN = "some_concern"
    INSUFFICIENT_PRE_TREATMENT_DATA = "insufficient_pre_treatment_data"
    NO_OBVIOUS_DIVERGENCE_ACROSS_REVIEWED_VARIANTS = (
        "no_obvious_divergence_across_reviewed_variants"
    )
    INSUFFICIENT_VARIANTS = "insufficient_variants"


class RobustnessVariant(FrozenPolarisBaseModel):
    variant_id: NonEmptyStr
    variant_type: RobustnessVariantType
    description: NonEmptyStr
    methodological_rationale: NonEmptyStr
    expected_diagnostic_purpose: NonEmptyStr
    pre_treatment_window: tuple[int | float, int | float] | None = None
    post_treatment_window: tuple[int | float, int | float] | None = None
    event_study_window: tuple[int, int] | None = None
    event_study_reference_period: int | None = None
    control_entities: tuple[NonEmptyStr, ...] | None = None
    covariates: tuple[VariableReference, ...] | None = None
    omitted_entity: NonEmptyStr | None = None
    placebo_treatment_start_period: int | float | None = None
    placebo_treated_entities: tuple[NonEmptyStr, ...] | None = None
    treatment_start_period: int | float | None = None
    confidence_level: float | None = Field(default=None, gt=0, lt=1)
    baseline_fields_preserved: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    minimum_required_observations: int | None = Field(default=None, ge=1)
    minimum_required_clusters: int | None = Field(default=None, ge=1)

    @field_validator("baseline_fields_preserved")
    @classmethod
    def sort_preserved(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("control_entities", "placebo_treated_entities")
    @classmethod
    def sort_entities(cls, value: tuple[str, ...] | None) -> tuple[str, ...] | None:
        if value is None:
            return None
        return tuple(sorted(set(value)))

    @field_validator("covariates")
    @classmethod
    def sort_covariates(
        cls, value: tuple[VariableReference, ...] | None
    ) -> tuple[VariableReference, ...] | None:
        if value is None:
            return None
        by_id = {item.variable_id: item for item in value}
        return tuple(by_id[key] for key in sorted(by_id))

    @model_validator(mode="after")
    def validate_variant_shape(self) -> RobustnessVariant:
        if self.variant_type is RobustnessVariantType.ALTERNATIVE_TIME_WINDOW and (
            self.pre_treatment_window is None or self.post_treatment_window is None
        ):
            raise ValueError("alternative time-window variants require pre and post windows")
        if (
            self.variant_type is RobustnessVariantType.ALTERNATIVE_CONTROL_GROUP
            and not self.control_entities
        ):
            raise ValueError("alternative control-group variants require explicit controls")
        if self.variant_type is RobustnessVariantType.COVARIATE_SET and self.covariates is None:
            raise ValueError("covariate variants require an explicit covariate set")
        if (
            self.variant_type
            in {
                RobustnessVariantType.LEAVE_ONE_TREATED_ENTITY_OUT,
                RobustnessVariantType.LEAVE_ONE_CONTROL_ENTITY_OUT,
            }
            and not self.omitted_entity
        ):
            raise ValueError("leave-one-out variants require omitted_entity")
        if (
            self.variant_type is RobustnessVariantType.PLACEBO_TIMING
            and self.placebo_treatment_start_period is None
        ):
            raise ValueError("placebo timing variants require an explicit placebo year")
        if (
            self.variant_type is RobustnessVariantType.PLACEBO_ASSIGNMENT
            and not self.placebo_treated_entities
        ):
            raise ValueError("placebo assignment variants require explicit placebo entities")
        if self.variant_type is RobustnessVariantType.EVENT_STUDY_WINDOW and (
            self.event_study_window is None or self.event_study_reference_period is None
        ):
            raise ValueError("event-study variants require window and reference period")
        if (
            self.variant_type is RobustnessVariantType.CONFIDENCE_LEVEL
            and self.confidence_level is None
        ):
            raise ValueError("confidence-level variants require confidence_level")
        if (
            self.variant_type is RobustnessVariantType.TREATMENT_TIMING
            and self.treatment_start_period is None
        ):
            raise ValueError("treatment-timing variants require explicit treatment_start_period")
        return self


class RobustnessSpecification(FrozenPolarisBaseModel):
    specification_id: NonEmptyStr
    baseline_analysis_id: NonEmptyStr
    study_id: NonEmptyStr | None = None
    intervention_id: NonEmptyStr | None = None
    treatment_provenance: dict[str, str] = Field(default_factory=dict)
    baseline_specification: CausalSpecification
    variants: tuple[RobustnessVariant, ...] = Field(default_factory=tuple)
    minimum_required_observations: int = Field(default=1, ge=1)
    minimum_required_clusters: int = Field(default=2, ge=1)
    strictness: RobustnessStrictness = RobustnessStrictness.STRICT
    schema_version: SchemaVersion = ROBUSTNESS_SCHEMA_VERSION
    ruleset_version: NonEmptyStr = ROBUSTNESS_RULESET_VERSION

    @field_validator("variants")
    @classmethod
    def unique_variant_ids(
        cls, value: tuple[RobustnessVariant, ...]
    ) -> tuple[RobustnessVariant, ...]:
        ids = [item.variant_id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("robustness variants require unique variant IDs")
        return tuple(sorted(value, key=lambda item: item.variant_id))

    @model_validator(mode="after")
    def require_matching_baseline(self) -> RobustnessSpecification:
        if self.baseline_analysis_id.strip() == "":
            raise ValueError("baseline_analysis_id is required")
        return self


class BaselineSpecificationSnapshot(FrozenPolarisBaseModel):
    baseline_analysis_id: NonEmptyStr
    study_id: NonEmptyStr | None = None
    intervention_id: NonEmptyStr | None = None
    treatment_provenance: dict[str, str] = Field(default_factory=dict)
    estimand: CausalEstimand
    method: CausalMethod
    controls: tuple[NonEmptyStr, ...]
    covariates: tuple[VariableId, ...] = Field(default_factory=tuple)
    event_window: tuple[int, int] | None = None
    event_reference_period: int | None = None
    pre_treatment_window: tuple[int | float, int | float]
    post_treatment_window: tuple[int | float, int | float]
    assumptions: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class VariantObservationChanges(FrozenPolarisBaseModel):
    included_row_numbers_added: tuple[int, ...] = Field(default_factory=tuple)
    included_row_numbers_removed: tuple[int, ...] = Field(default_factory=tuple)
    excluded_entities: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class RobustnessVariantResult(FrozenPolarisBaseModel):
    variant_id: NonEmptyStr
    variant_type: RobustnessVariantType
    analysis_result: CausalAnalysisResult
    observation_changes: VariantObservationChanges
    estimate_difference_from_baseline: float | None = None
    confidence_interval_overlaps_baseline: bool | None = None


class FailedRobustnessVariant(FrozenPolarisBaseModel):
    variant_id: NonEmptyStr
    variant_type: RobustnessVariantType
    error_type: NonEmptyStr
    reason: NonEmptyStr
    methodological_implication: NonEmptyStr


class TreatmentEffectStabilitySummary(FrozenPolarisBaseModel):
    baseline_estimate: float | None
    minimum_estimate: float | None
    maximum_estimate: float | None
    median_estimate: float | None
    number_positive: int = Field(ge=0)
    number_negative: int = Field(ge=0)
    number_crossing_zero: int = Field(ge=0)
    successful_variant_count: int = Field(ge=0)


class SignificanceStabilitySummary(FrozenPolarisBaseModel):
    significance_threshold: float | None = None
    baseline_significant: bool | None = None
    significant_variant_count: int = Field(ge=0)
    nonsignificant_variant_count: int = Field(ge=0)
    changed_relative_to_baseline_count: int = Field(ge=0)


class LeaveOneOutResult(FrozenPolarisBaseModel):
    variant_id: NonEmptyStr
    omitted_entity: NonEmptyStr
    omitted_role: NonEmptyStr
    treatment_estimate: float | None
    standard_error: float | None = None
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    p_value: float | None = None
    sample_size: int = Field(ge=0)
    cluster_count: int = Field(ge=0)
    difference_from_baseline: float | None = None
    low_cluster_warning: bool = False


class PlaceboResult(FrozenPolarisBaseModel):
    variant_id: NonEmptyStr
    placebo_year: int | float | None = None
    placebo_treated_entities: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    estimate: float | None
    standard_error: float | None = None
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    p_value: float | None = None
    sample_size: int = Field(ge=0)
    cluster_count: int = Field(ge=0)
    diagnostic_interpretation: NonEmptyStr


class EventStudyComparisonRecord(FrozenPolarisBaseModel):
    variant_id: NonEmptyStr
    event_time: int
    estimate: float | None
    standard_error: float | None = None
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    p_value: float | None = None
    pre_post_status: NonEmptyStr
    omitted_reference_period: int


class PreTrendRobustnessSummary(FrozenPolarisBaseModel):
    status: ParallelTrendRobustnessStatus
    diagnostics_by_variant: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    interpretation: NonEmptyStr


class RobustnessComparisonSummary(FrozenPolarisBaseModel):
    variant_type: RobustnessVariantType
    successful_specifications: int = Field(ge=0)
    failed_specifications: int = Field(ge=0)
    estimate_minimum: float | None = None
    estimate_maximum: float | None = None
    estimate_median: float | None = None


class RobustnessProvenance(FrozenPolarisBaseModel):
    dataset_id: DatasetId
    source_checksum_sha256: str
    baseline_analysis_id: NonEmptyStr
    baseline_specification: CausalSpecification
    variant_specifications: tuple[RobustnessVariant, ...]
    study_id: NonEmptyStr | None = None
    intervention_id: NonEmptyStr | None = None
    treatment_sources: dict[str, str] = Field(default_factory=dict)
    excluded_observations_by_variant: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    estimator_version: NonEmptyStr
    schema_version: SchemaVersion = ROBUSTNESS_SCHEMA_VERSION
    ruleset_version: NonEmptyStr = ROBUSTNESS_RULESET_VERSION
    software_version: NonEmptyStr = f"polaris-{__version__}"


class RealStudyReadinessBlock(FrozenPolarisBaseModel):
    study_id: NonEmptyStr
    readiness_status: NonEmptyStr
    review_status: NonEmptyStr
    blocking_reasons: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    assessment: DesignReadinessAssessment | None = None


class RobustnessAnalysisResult(FrozenPolarisBaseModel):
    robustness_analysis_id: NonEmptyStr
    study_id: NonEmptyStr | None = None
    baseline: BaselineSpecificationSnapshot
    baseline_result: CausalAnalysisResult
    variants: tuple[RobustnessVariant, ...]
    variant_results: tuple[RobustnessVariantResult, ...] = Field(default_factory=tuple)
    failed_variants: tuple[FailedRobustnessVariant, ...] = Field(default_factory=tuple)
    comparison_summaries: tuple[RobustnessComparisonSummary, ...] = Field(default_factory=tuple)
    treatment_effect_stability: TreatmentEffectStabilitySummary
    significance_stability: SignificanceStabilitySummary
    robustness_evidence_status: RobustnessEvidenceStatus
    pre_trend_diagnostics: PreTrendRobustnessSummary
    leave_one_out_results: tuple[LeaveOneOutResult, ...] = Field(default_factory=tuple)
    placebo_results: tuple[PlaceboResult, ...] = Field(default_factory=tuple)
    event_study_comparison: tuple[EventStudyComparisonRecord, ...] = Field(default_factory=tuple)
    limitations: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    real_study_readiness_blocks: tuple[RealStudyReadinessBlock, ...] = Field(default_factory=tuple)
    plotting_artifacts: dict[str, tuple[dict[str, Any], ...]] = Field(default_factory=dict)
    provenance: RobustnessProvenance
    analysis_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    software_version: NonEmptyStr = f"polaris-{__version__}"
    schema_version: SchemaVersion = ROBUSTNESS_SCHEMA_VERSION
    ruleset_version: NonEmptyStr = ROBUSTNESS_RULESET_VERSION
