"""Typed contracts for deterministic structured evidence and claim candidates."""

import math
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from polaris.analysis.models import AnalysisFindingCode
from polaris.schemas.common import (
    AwareDatetime,
    DatasetId,
    FrozenPolarisBaseModel,
    NonEmptyStr,
    SchemaVersion,
    StatisticalProcedure,
    VariableId,
)

EVIDENCE_SCHEMA_VERSION = "1.0.0"


class EvidenceType(StrEnum):
    DESCRIPTIVE_SUMMARY = "descriptive_summary"
    CORRELATION = "correlation"
    REGRESSION_COEFFICIENT = "regression_coefficient"
    MODEL_FIT = "model_fit"
    MODEL_DIAGNOSTIC = "model_diagnostic"
    SAMPLE_QUALITY = "sample_quality"
    ANALYSIS_WARNING = "analysis_warning"
    CAUSAL_TREATMENT_EFFECT = "causal_treatment_effect"
    CAUSAL_ASSUMPTION = "causal_assumption"
    CAUSAL_DIAGNOSTIC = "causal_diagnostic"


class Direction(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    ZERO = "zero"
    UNDEFINED = "undefined"
    NOT_APPLICABLE = "not_applicable"


class ClaimType(StrEnum):
    DESCRIPTIVE_OBSERVATION = "descriptive_observation"
    ASSOCIATION = "association"
    CONDITIONAL_ASSOCIATION = "conditional_association"
    STATISTICAL_UNCERTAINTY = "statistical_uncertainty"
    MODEL_LIMITATION = "model_limitation"
    CAUSAL_DESIGN_ESTIMATE = "causal_design_estimate"


class LimitationCode(StrEnum):
    MISSING_DATA_EXCLUSION = "MISSING_DATA_EXCLUSION"
    SMALL_SAMPLE = "SMALL_SAMPLE"
    CONSTANT_VARIABLE = "CONSTANT_VARIABLE"
    SINGULAR_DESIGN_MATRIX = "SINGULAR_DESIGN_MATRIX"
    MULTICOLLINEARITY = "MULTICOLLINEARITY"
    HETEROSKEDASTICITY_WARNING = "HETEROSKEDASTICITY_WARNING"
    RESIDUAL_NORMALITY_WARNING = "RESIDUAL_NORMALITY_WARNING"
    UNDEFINED_DIAGNOSTIC = "UNDEFINED_DIAGNOSTIC"
    PERFECT_CORRELATION = "PERFECT_CORRELATION"
    LIMITED_MODEL_SCOPE = "LIMITED_MODEL_SCOPE"
    OBSERVATIONAL_ASSOCIATION = "OBSERVATIONAL_ASSOCIATION"
    UNSUPPORTED_GENERALIZATION = "UNSUPPORTED_GENERALIZATION"
    PANEL_UNBALANCED = "PANEL_UNBALANCED"
    LOW_CLUSTER_COUNT = "LOW_CLUSTER_COUNT"
    LOW_WITHIN_VARIATION = "LOW_WITHIN_VARIATION"
    SERIAL_CORRELATION_CAUTION = "SERIAL_CORRELATION_CAUTION"
    CROSS_SECTIONAL_DEPENDENCE_LIMITATION = "CROSS_SECTIONAL_DEPENDENCE_LIMITATION"
    CONDITIONAL_CAUSAL_DESIGN = "CONDITIONAL_CAUSAL_DESIGN"
    IDENTIFICATION_ASSUMPTION_LIMITATION = "IDENTIFICATION_ASSUMPTION_LIMITATION"
    PRE_TREND_CONCERN = "PRE_TREND_CONCERN"
    INSUFFICIENT_PRE_TREATMENT_DATA = "INSUFFICIENT_PRE_TREATMENT_DATA"
    LOW_TREATED_COUNT = "LOW_TREATED_COUNT"
    BAD_CONTROL_CAUTION = "BAD_CONTROL_CAUTION"


class ExtractionFindingCode(StrEnum):
    UNSUPPORTED_SOURCE_RESULT = "unsupported_source_result"
    EVIDENCE_EXTRACTED = "evidence_extracted"
    CLAIM_GENERATED = "claim_generated"
    CLAIM_SKIPPED = "claim_skipped"


class ExtractionFinding(FrozenPolarisBaseModel):
    code: ExtractionFindingCode
    message: NonEmptyStr
    evidence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    claim_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class EvidenceProvenance(FrozenPolarisBaseModel):
    dataset_id: DatasetId
    source_checksum_sha256: str
    source_analysis_result_id: NonEmptyStr
    statistical_procedure: StatisticalProcedure
    phase4_schema_version: SchemaVersion
    phase5_schema_version: SchemaVersion = EVIDENCE_SCHEMA_VERSION
    extraction_timestamp: AwareDatetime
    software_version: NonEmptyStr
    extraction_settings: tuple[NonEmptyStr, ...] = Field(default=("deterministic_phase5_v1",))


class EvidenceRecordBase(FrozenPolarisBaseModel):
    evidence_id: NonEmptyStr
    evidence_type: EvidenceType
    source_analysis_result_id: NonEmptyStr
    dataset_id: DatasetId
    source_checksum_sha256: str
    statistical_procedure: StatisticalProcedure
    sample_size: int | None = Field(default=None, ge=0)
    diagnostic_flags: tuple[AnalysisFindingCode, ...] = Field(default_factory=tuple)
    limitation_codes: tuple[LimitationCode, ...] = Field(default_factory=tuple)
    schema_version: SchemaVersion = EVIDENCE_SCHEMA_VERSION
    provenance: EvidenceProvenance

    @field_validator("*", check_fields=False)
    @classmethod
    def require_json_safe_numbers(cls, value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("evidence numeric fields must be finite or None")
        return value

    @field_validator("limitation_codes")
    @classmethod
    def sort_limitations(cls, value: tuple[LimitationCode, ...]) -> tuple[LimitationCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))


class DescriptiveEvidenceRecord(EvidenceRecordBase):
    evidence_type: Literal[EvidenceType.DESCRIPTIVE_SUMMARY] = EvidenceType.DESCRIPTIVE_SUMMARY
    variable_id: VariableId
    variable_type: NonEmptyStr
    summary_kind: Literal["numeric", "categorical"]
    count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    mean: float | None = None
    standard_deviation: float | None = None
    minimum: float | None = None
    percentile_25: float | None = None
    median: float | None = None
    percentile_75: float | None = None
    maximum: float | None = None
    unique_count: int | None = Field(default=None, ge=0)
    most_frequent_value: str | bool | None = None
    most_frequent_value_count: int | None = Field(default=None, ge=0)


class CorrelationEvidenceRecord(EvidenceRecordBase):
    evidence_type: Literal[EvidenceType.CORRELATION] = EvidenceType.CORRELATION
    variable_id_1: VariableId
    variable_id_2: VariableId
    method: Literal["pearson", "spearman"]
    correlation_coefficient: float | None = None
    p_value: float | None = None
    observation_count: int = Field(ge=0)
    defined: bool
    direction: Direction
    excluded_row_numbers: tuple[int, ...] = Field(default_factory=tuple)
    missing_exclusion_count: int = Field(ge=0)


class RegressionCoefficientEvidenceRecord(EvidenceRecordBase):
    evidence_type: Literal[EvidenceType.REGRESSION_COEFFICIENT] = (
        EvidenceType.REGRESSION_COEFFICIENT
    )
    dependent_variable_id: VariableId
    term: NonEmptyStr
    variable_id: VariableId | None = None
    estimate: float | None
    standard_error: float | None
    test_statistic: float | None
    p_value: float | None
    confidence_interval_low: float | None
    confidence_interval_high: float | None
    below_significance_threshold: bool | None = None
    direction: Direction
    is_intercept: bool
    model_result_id: NonEmptyStr
    predictor_variable_ids: tuple[VariableId, ...] = Field(default_factory=tuple)


class ModelFitEvidenceRecord(EvidenceRecordBase):
    evidence_type: Literal[EvidenceType.MODEL_FIT] = EvidenceType.MODEL_FIT
    dependent_variable_id: VariableId
    predictor_variable_ids: tuple[VariableId, ...] = Field(default_factory=tuple)
    r_squared: float | None
    adjusted_r_squared: float | None
    residual_degrees_of_freedom: float
    model_degrees_of_freedom: float
    residual_sum_of_squares: float | None
    mean_squared_error: float | None
    model_result_id: NonEmptyStr


class DiagnosticEvidenceRecord(EvidenceRecordBase):
    evidence_type: Literal[EvidenceType.MODEL_DIAGNOSTIC] = EvidenceType.MODEL_DIAGNOSTIC
    diagnostic_type: NonEmptyStr
    status: NonEmptyStr
    statistic: float | None = None
    p_value: float | None = None
    variable_id: VariableId | None = None
    threshold: float | None = None
    warning_codes: tuple[AnalysisFindingCode, ...] = Field(default_factory=tuple)


class SampleQualityEvidenceRecord(EvidenceRecordBase):
    evidence_type: Literal[EvidenceType.SAMPLE_QUALITY] = EvidenceType.SAMPLE_QUALITY
    required_variable_ids: tuple[VariableId, ...] = Field(default_factory=tuple)
    original_accepted_record_count: int = Field(ge=0)
    final_analysis_sample_size: int = Field(ge=0)
    excluded_row_count: int = Field(ge=0)
    exclusion_reason_counts: tuple[tuple[NonEmptyStr, int], ...] = Field(default_factory=tuple)
    missing_value_exclusion_count: int = Field(ge=0)
    accepted_records_used_percentage: float | None = None
    included_row_numbers: tuple[int, ...] = Field(default_factory=tuple)
    excluded_row_numbers: tuple[int, ...] = Field(default_factory=tuple)


class AnalysisWarningEvidenceRecord(EvidenceRecordBase):
    evidence_type: Literal[EvidenceType.ANALYSIS_WARNING] = EvidenceType.ANALYSIS_WARNING
    finding_code: AnalysisFindingCode
    severity: NonEmptyStr
    variable_ids: tuple[VariableId, ...] = Field(default_factory=tuple)
    method: str | None = None
    statistic: float | None = None
    threshold: float | None = None
    source_row_numbers: tuple[int, ...] = Field(default_factory=tuple)


class CausalTreatmentEffectEvidenceRecord(EvidenceRecordBase):
    evidence_type: Literal[EvidenceType.CAUSAL_TREATMENT_EFFECT] = (
        EvidenceType.CAUSAL_TREATMENT_EFFECT
    )
    causal_method: NonEmptyStr
    estimator: NonEmptyStr
    estimand: NonEmptyStr
    outcome_variable_id: VariableId
    treatment_variable_id: VariableId
    estimate: float | None
    standard_error: float | None = None
    p_value: float | None = None
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    cluster_count: int | None = Field(default=None, ge=0)
    treated_entity_count: int = Field(ge=0)
    control_entity_count: int = Field(ge=0)
    assumption_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class CausalAssumptionEvidenceRecord(EvidenceRecordBase):
    evidence_type: Literal[EvidenceType.CAUSAL_ASSUMPTION] = EvidenceType.CAUSAL_ASSUMPTION
    assumption_code: NonEmptyStr
    status: NonEmptyStr
    description: NonEmptyStr
    diagnostic_evidence: NonEmptyStr | None = None
    limitation: NonEmptyStr | None = None
    empirically_testable: bool


class CausalDiagnosticEvidenceRecord(EvidenceRecordBase):
    evidence_type: Literal[EvidenceType.CAUSAL_DIAGNOSTIC] = EvidenceType.CAUSAL_DIAGNOSTIC
    diagnostic_type: NonEmptyStr
    status: NonEmptyStr
    pre_treatment_period_count: int = Field(ge=0)
    diagnostic_summary: NonEmptyStr
    event_study_plot_data: tuple[dict[str, object], ...] = Field(default_factory=tuple)


EvidenceRecord = Annotated[
    DescriptiveEvidenceRecord
    | CorrelationEvidenceRecord
    | RegressionCoefficientEvidenceRecord
    | ModelFitEvidenceRecord
    | DiagnosticEvidenceRecord
    | SampleQualityEvidenceRecord
    | AnalysisWarningEvidenceRecord
    | CausalTreatmentEffectEvidenceRecord
    | CausalAssumptionEvidenceRecord
    | CausalDiagnosticEvidenceRecord,
    Field(discriminator="evidence_type"),
]


class ClaimCandidate(FrozenPolarisBaseModel):
    claim_id: NonEmptyStr
    claim_type: ClaimType
    subject_variable: VariableId | None = None
    outcome_variable: VariableId | None = None
    related_variables: tuple[VariableId, ...] = Field(default_factory=tuple)
    direction: Direction = Direction.NOT_APPLICABLE
    statistical_procedure: StatisticalProcedure
    supporting_evidence_ids: tuple[NonEmptyStr, ...] = Field(min_length=1)
    limitation_codes: tuple[LimitationCode, ...] = Field(default_factory=tuple)
    causal: bool = False
    generalization_scope: Literal["analysis_sample"] = "analysis_sample"
    source_analysis_result_id: NonEmptyStr
    dataset_id: DatasetId
    schema_version: SchemaVersion = EVIDENCE_SCHEMA_VERSION
    provenance: EvidenceProvenance
    p_value_below_threshold: bool | None = None
    confidence_interval_crosses_zero: bool | None = None

    @field_validator("*", check_fields=False)
    @classmethod
    def require_json_safe_numbers(cls, value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("claim numeric fields must be finite or None")
        return value

    @field_validator("related_variables", "supporting_evidence_ids")
    @classmethod
    def sort_strings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("limitation_codes")
    @classmethod
    def sort_claim_limitations(
        cls, value: tuple[LimitationCode, ...]
    ) -> tuple[LimitationCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @model_validator(mode="after")
    def prohibit_unsupported_causal_claims(self) -> "ClaimCandidate":
        if self.causal and self.claim_type is not ClaimType.CAUSAL_DESIGN_ESTIMATE:
            raise ValueError("causal claims require claim_type=causal_design_estimate")
        if self.claim_type is ClaimType.CAUSAL_DESIGN_ESTIMATE and not self.causal:
            raise ValueError("causal-design estimate claims must be marked causal")
        return self


class EvidenceArtifact(FrozenPolarisBaseModel):
    artifact_id: NonEmptyStr
    source_analysis_result_id: NonEmptyStr
    dataset_id: DatasetId
    source_checksum_sha256: str
    evidence_records: tuple[EvidenceRecord, ...] = Field(default_factory=tuple)
    claim_candidates: tuple[ClaimCandidate, ...] = Field(default_factory=tuple)
    extraction_findings: tuple[ExtractionFinding, ...] = Field(default_factory=tuple)
    provenance: EvidenceProvenance
    extraction_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    software_version: NonEmptyStr
    schema_version: SchemaVersion = EVIDENCE_SCHEMA_VERSION
