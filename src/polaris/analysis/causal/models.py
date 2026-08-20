"""Typed contracts for explicit causal research designs."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from polaris import __version__
from polaris.analysis.models import (
    AnalysisFinding,
    AnalysisSampleSummary,
    PanelRegressionResult,
    RegressionCoefficient,
)
from polaris.ingestion.models import DatasetIngestionResult
from polaris.schemas.common import (
    AwareDatetime,
    DatasetId,
    FrozenPolarisBaseModel,
    InvestigationId,
    NonEmptyStr,
    SchemaVersion,
    SpecificationId,
    VariableId,
    VariableReference,
)
from polaris.schemas.statistics import StandardErrorSpec

CAUSAL_SCHEMA_VERSION = "1.0.0"
CAUSAL_RULESET_VERSION = "causal_foundations_phase22_v1"


class CausalMethod(StrEnum):
    DIFFERENCE_IN_DIFFERENCES = "difference_in_differences"
    EVENT_STUDY = "event_study"


class CausalEstimator(StrEnum):
    SIMPLE_DID = "simple_did"
    TWFE_DID = "twfe_did"
    TWFE_EVENT_STUDY = "twfe_event_study"


class CausalEstimand(StrEnum):
    ATT = "att"


class DesignAssumptionCode(StrEnum):
    PARALLEL_TRENDS = "parallel_trends"
    NO_ANTICIPATION = "no_anticipation"
    STABLE_TREATMENT_DEFINITION = "stable_treatment_definition"
    NO_TREATMENT_CONTAMINATION = "no_treatment_contamination"
    CONSISTENT_OUTCOME_MEASUREMENT = "consistent_outcome_measurement"
    APPROPRIATE_COMPARISON_GROUP = "appropriate_comparison_group"
    NO_DIFFERENTIAL_COMPOSITIONAL_CHANGE = "no_differential_compositional_change"
    SUTVA_SPILLOVER = "sutva_spillover"


class DesignAssumptionStatus(StrEnum):
    SUPPORTED_BY_DIAGNOSTIC = "supported_by_diagnostic"
    NOT_VIOLATED_BY_AVAILABLE_DIAGNOSTIC = "not_violated_by_available_diagnostic"
    CONCERN = "concern"
    INSUFFICIENT_INFORMATION = "insufficient_information"
    UNTESTABLE = "untestable"


class ParallelTrendDiagnosticStatus(StrEnum):
    NO_OBVIOUS_PRE_TREATMENT_DIVERGENCE_DETECTED = "no_obvious_pre_treatment_divergence_detected"
    CONCERNING_PRE_TREATMENT_EVIDENCE_DETECTED = "concerning_pre_treatment_evidence_detected"
    INSUFFICIENT_PRE_TREATMENT_DATA = "insufficient_pre_treatment_data"
    DIAGNOSTIC_INCONCLUSIVE = "diagnostic_inconclusive"


class CausalFixedEffectsConfig(FrozenPolarisBaseModel):
    entity_fixed_effects: bool = True
    time_fixed_effects: bool = True


class EventStudyConfig(FrozenPolarisBaseModel):
    min_event_time: int
    max_event_time: int
    reference_event_time: int

    @model_validator(mode="after")
    def validate_window(self) -> "EventStudyConfig":
        if self.min_event_time >= self.max_event_time:
            raise ValueError("event-study window requires min_event_time < max_event_time")
        if not self.min_event_time <= self.reference_event_time <= self.max_event_time:
            raise ValueError("reference_event_time must fall inside the event window")
        return self


class TreatmentAssignment(FrozenPolarisBaseModel):
    treatment_variable: VariableReference
    treated_value: str | int | float | bool = 1
    control_value: str | int | float | bool = 0
    treatment_start_period: int | float | None = None
    treatment_timing_variable: VariableReference | None = None
    absorbing: bool = True
    treatment_source: NonEmptyStr = "explicit_user_specification"

    @model_validator(mode="after")
    def require_timing(self) -> "TreatmentAssignment":
        if self.treatment_start_period is None and self.treatment_timing_variable is None:
            raise ValueError("causal treatment assignment requires explicit treatment timing")
        if self.treated_value == self.control_value:
            raise ValueError("treated and control values must differ")
        return self


class CausalSpecification(FrozenPolarisBaseModel):
    specification_id: SpecificationId
    investigation_id: InvestigationId
    method: CausalMethod
    entity_variable: VariableReference
    time_variable: VariableReference
    outcome_variable: VariableReference
    treatment: TreatmentAssignment
    treated_group_description: NonEmptyStr
    comparison_group_description: NonEmptyStr
    pre_treatment_window: tuple[int | float, int | float]
    post_treatment_window: tuple[int | float, int | float]
    covariates: tuple[VariableReference, ...] = Field(default_factory=tuple)
    fixed_effects: CausalFixedEffectsConfig = Field(default_factory=CausalFixedEffectsConfig)
    standard_error_strategy: StandardErrorSpec
    estimand: CausalEstimand
    event_study: EventStudyConfig | None = None
    confidence_level: float = Field(default=0.95, gt=0, lt=1)
    strict_covariate_timing: bool = True
    acknowledged_post_treatment_covariates: tuple[VariableId, ...] = Field(default_factory=tuple)
    assumptions: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    registry_provenance: dict[str, str] = Field(default_factory=dict)
    schema_version: SchemaVersion = CAUSAL_SCHEMA_VERSION

    @field_validator("covariates")
    @classmethod
    def sort_unique_covariates(
        cls, value: tuple[VariableReference, ...]
    ) -> tuple[VariableReference, ...]:
        by_id = {item.variable_id: item for item in value}
        return tuple(by_id[key] for key in sorted(by_id))

    @field_validator("acknowledged_post_treatment_covariates")
    @classmethod
    def sort_unique_covariate_acknowledgements(
        cls, value: tuple[VariableId, ...]
    ) -> tuple[VariableId, ...]:
        return tuple(sorted(set(value)))

    @model_validator(mode="after")
    def validate_design_shape(self) -> "CausalSpecification":
        if self.pre_treatment_window[0] > self.pre_treatment_window[1]:
            raise ValueError("pre_treatment_window must be ordered")
        if self.post_treatment_window[0] > self.post_treatment_window[1]:
            raise ValueError("post_treatment_window must be ordered")
        if self.pre_treatment_window[1] >= self.post_treatment_window[0]:
            raise ValueError("pre-treatment window must precede post-treatment window")
        if self.method is CausalMethod.EVENT_STUDY and self.event_study is None:
            raise ValueError("event-study designs require event_study configuration")
        if self.method is CausalMethod.DIFFERENCE_IN_DIFFERENCES and self.event_study is not None:
            raise ValueError("DiD designs must not include event-study configuration")
        cluster_ids = tuple(
            item.variable_id for item in self.standard_error_strategy.cluster_variables
        )
        if cluster_ids != (self.entity_variable.variable_id,):
            raise ValueError("Phase 22 supports entity-clustered causal inference only")
        return self


class CausalAnalysisRequest(FrozenPolarisBaseModel):
    ingestion_result: DatasetIngestionResult
    causal_specification: CausalSpecification
    significance_threshold: float | None = Field(default=None, gt=0, lt=1)
    confidence_level: float | None = Field(default=None, gt=0, lt=1)

    @model_validator(mode="after")
    def require_analysis_ready_ingestion(self) -> "CausalAnalysisRequest":
        if not self.ingestion_result.validation_report.analysis_ready:
            raise ValueError("causal analysis requires an analysis-ready ingestion result")
        return self

    @property
    def effective_confidence_level(self) -> float:
        return self.confidence_level or self.causal_specification.confidence_level


class CausalSampleSummary(FrozenPolarisBaseModel):
    input_rows: int = Field(ge=0)
    included_rows: int = Field(ge=0)
    excluded_rows: int = Field(ge=0)
    treated_entity_count: int = Field(ge=0)
    control_entity_count: int = Field(ge=0)
    cluster_count: int = Field(ge=0)
    pre_period_count: int = Field(ge=0)
    post_period_count: int = Field(ge=0)
    event_window_excluded_rows: int = Field(ge=0)
    included_row_numbers: tuple[int, ...] = Field(default_factory=tuple)
    excluded_row_numbers: tuple[int, ...] = Field(default_factory=tuple)


class DIDComponentMeans(FrozenPolarisBaseModel):
    treated_pre_mean: float
    treated_post_mean: float
    control_pre_mean: float
    control_post_mean: float
    treated_difference: float
    control_difference: float


class TreatmentEffectEstimate(FrozenPolarisBaseModel):
    estimator: CausalEstimator
    estimand: CausalEstimand
    term: NonEmptyStr
    estimate: float | None
    standard_error: float | None = None
    test_statistic: float | None = None
    p_value: float | None = None
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    standard_error_type: NonEmptyStr | None = None
    cluster_count: int | None = Field(default=None, ge=0)
    component_means: DIDComponentMeans | None = None
    coefficient: RegressionCoefficient | None = None


class EventStudyCoefficient(FrozenPolarisBaseModel):
    event_time: int
    coefficient: float | None
    standard_error: float | None
    confidence_interval_low: float | None
    confidence_interval_high: float | None
    p_value: float | None
    observation_count: int = Field(ge=0)
    treated_entity_count: int = Field(ge=0)
    reference_period: bool = False
    pre_post_status: Literal["pre", "reference", "post"]


class ParallelTrendsDiagnostic(FrozenPolarisBaseModel):
    status: ParallelTrendDiagnosticStatus
    pre_treatment_period_count: int = Field(ge=0)
    pre_treatment_coefficients: tuple[EventStudyCoefficient, ...] = Field(default_factory=tuple)
    trend_summary: NonEmptyStr
    joint_diagnostic: NonEmptyStr | None = None
    data_sufficiency: NonEmptyStr


class DesignAssumptionRecord(FrozenPolarisBaseModel):
    assumption_code: DesignAssumptionCode
    description: NonEmptyStr
    status: DesignAssumptionStatus
    diagnostic_evidence: NonEmptyStr | None = None
    limitation: NonEmptyStr | None = None
    empirically_testable: bool
    provenance: dict[str, str] = Field(default_factory=dict)


class CausalDesignDiagnostics(FrozenPolarisBaseModel):
    structural_validation_passed: bool
    treatment_integrity_passed: bool
    parallel_trends: ParallelTrendsDiagnostic
    warnings: tuple[AnalysisFinding, ...] = Field(default_factory=tuple)


class CausalProvenance(FrozenPolarisBaseModel):
    dataset_id: DatasetId
    source_checksum_sha256: str
    ingestion_timestamp: AwareDatetime
    specification: CausalSpecification
    treatment_source: NonEmptyStr
    treatment_assignment_variable: VariableId
    treatment_timing_variable: VariableId | None = None
    entity_variable_id: VariableId
    time_variable_id: VariableId
    outcome_variable_id: VariableId
    covariate_ids: tuple[VariableId, ...] = Field(default_factory=tuple)
    registry_provenance: dict[str, str] = Field(default_factory=dict)
    included_row_numbers: tuple[int, ...] = Field(default_factory=tuple)
    excluded_row_numbers: tuple[int, ...] = Field(default_factory=tuple)
    analysis_timestamp: AwareDatetime
    software_version: NonEmptyStr = f"polaris-{__version__}"
    schema_version: SchemaVersion = CAUSAL_SCHEMA_VERSION
    ruleset_version: NonEmptyStr = CAUSAL_RULESET_VERSION


class CausalAnalysisResult(FrozenPolarisBaseModel):
    causal_analysis_id: NonEmptyStr
    method: CausalMethod
    estimator: CausalEstimator
    causal_specification: CausalSpecification
    dataset_id: DatasetId
    source_checksum_sha256: str
    estimand: CausalEstimand
    treatment_effect: TreatmentEffectEstimate
    regression_result: PanelRegressionResult | None = None
    sample_summary: CausalSampleSummary
    analysis_sample: AnalysisSampleSummary
    event_study_results: tuple[EventStudyCoefficient, ...] = Field(default_factory=tuple)
    assumptions: tuple[DesignAssumptionRecord, ...] = Field(default_factory=tuple)
    diagnostics: CausalDesignDiagnostics
    limitations: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    findings: tuple[AnalysisFinding, ...] = Field(default_factory=tuple)
    provenance: CausalProvenance
    analysis_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    software_version: NonEmptyStr = f"polaris-{__version__}"
    schema_version: SchemaVersion = CAUSAL_SCHEMA_VERSION
    ruleset_version: NonEmptyStr = CAUSAL_RULESET_VERSION
