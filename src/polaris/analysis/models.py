"""Typed contracts for deterministic statistical analysis results."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from polaris.ingestion.models import DatasetIngestionResult
from polaris.schemas.common import (
    AwareDatetime,
    DatasetId,
    FrozenPolarisBaseModel,
    NonEmptyStr,
    SchemaVersion,
    StatisticalProcedure,
    VariableId,
)
from polaris.schemas.provenance import ProvenanceRecord
from polaris.schemas.statistics import StatisticalSpecification

ANALYSIS_SCHEMA_VERSION = "1.0.0"


class MissingDataPolicy(StrEnum):
    COMPLETE_CASE = "complete_case"


class FindingSeverity(StrEnum):
    FATAL = "fatal"
    WARNING = "warning"
    INFO = "info"


class AnalysisFindingCode(StrEnum):
    MISSING_VARIABLE = "missing_variable"
    INCOMPATIBLE_VARIABLE_TYPE = "incompatible_variable_type"
    INSUFFICIENT_OBSERVATIONS = "insufficient_observations"
    CONSTANT_VARIABLE = "constant_variable"
    ALL_NULL_VARIABLE = "all_null_variable"
    EXCLUDED_MISSING_ROWS = "excluded_missing_rows"
    PERFECT_CORRELATION = "perfect_correlation"
    SINGULAR_DESIGN_MATRIX = "singular_design_matrix"
    MULTICOLLINEARITY = "multicollinearity"
    HETEROSKEDASTICITY_TEST_RESULT = "heteroskedasticity_test_result"
    RESIDUAL_NORMALITY_TEST_RESULT = "residual_normality_test_result"
    UNSUPPORTED_SPECIFICATION_OPTION = "unsupported_specification_option"
    UNSUPPORTED_METHOD = "unsupported_method"
    DIAGNOSTIC_NOT_APPLICABLE = "diagnostic_not_applicable"
    CAUSAL_INTERPRETATION_UNSUPPORTED = "causal_interpretation_unsupported"
    UNDEFINED_STATISTIC = "undefined_statistic"
    DUPLICATE_PANEL_KEY = "duplicate_panel_key"
    INSUFFICIENT_PANEL_DATA = "insufficient_panel_data"
    LOW_CLUSTER_COUNT = "low_cluster_count"
    LAG_EXCLUDED_ROWS = "lag_excluded_rows"
    TIME_INVARIANT_PREDICTOR = "time_invariant_predictor"
    UNBALANCED_PANEL = "unbalanced_panel"
    LOW_WITHIN_VARIATION = "low_within_variation"
    SERIAL_CORRELATION_CAUTION = "serial_correlation_caution"
    CROSS_SECTIONAL_DEPENDENCE_LIMITATION = "cross_sectional_dependence_limitation"


class DiagnosticStatus(StrEnum):
    CALCULATED = "calculated"
    UNDEFINED = "undefined"
    NOT_APPLICABLE = "not_applicable"


class AnalysisExecutionSettings(FrozenPolarisBaseModel):
    missing_data_policy: MissingDataPolicy = MissingDataPolicy.COMPLETE_CASE
    include_intercept: bool = True
    pairwise_correlation: bool = False


class AnalysisRequest(FrozenPolarisBaseModel):
    ingestion_result: DatasetIngestionResult
    statistical_specification: StatisticalSpecification
    execution_settings: AnalysisExecutionSettings = Field(default_factory=AnalysisExecutionSettings)
    significance_threshold: float | None = Field(default=None, gt=0, lt=1)
    confidence_level: float | None = Field(default=None, gt=0, lt=1)

    @model_validator(mode="after")
    def require_analysis_ready_ingestion(self) -> "AnalysisRequest":
        if not self.ingestion_result.validation_report.analysis_ready:
            raise ValueError("analysis requires an analysis-ready ingestion result")
        return self

    @property
    def effective_confidence_level(self) -> float:
        return self.confidence_level or self.statistical_specification.confidence_level


class AnalysisFinding(FrozenPolarisBaseModel):
    severity: FindingSeverity
    code: AnalysisFindingCode
    message: NonEmptyStr
    variable_ids: tuple[VariableId, ...] = Field(default_factory=tuple)
    method: str | None = None
    statistic: float | None = None
    threshold: float | None = None
    source_row_numbers: tuple[int, ...] = Field(default_factory=tuple)

    @field_validator("statistic", "threshold")
    @classmethod
    def require_finite(cls, value: float | None) -> float | None:
        if value is None:
            return None
        if value != value or value in {float("inf"), float("-inf")}:
            raise ValueError("analysis numeric fields must be finite or None")
        return float(value)


class RowExclusion(FrozenPolarisBaseModel):
    row_number: int
    source_line_number: int
    reason: NonEmptyStr
    variable_ids: tuple[VariableId, ...] = Field(default_factory=tuple)


class AnalysisSample(FrozenPolarisBaseModel):
    variable_ids: tuple[VariableId, ...]
    rows: tuple[dict[str, int | float | str | bool], ...] = Field(default_factory=tuple)
    included_row_numbers: tuple[int, ...] = Field(default_factory=tuple)
    included_source_line_numbers: tuple[int, ...] = Field(default_factory=tuple)
    exclusions: tuple[RowExclusion, ...] = Field(default_factory=tuple)

    @property
    def sample_size(self) -> int:
        return len(self.rows)


class AnalysisSampleSummary(FrozenPolarisBaseModel):
    required_variable_ids: tuple[VariableId, ...]
    sample_size: int = Field(ge=0)
    included_row_numbers: tuple[int, ...] = Field(default_factory=tuple)
    excluded_row_numbers: tuple[int, ...] = Field(default_factory=tuple)
    exclusions: tuple[RowExclusion, ...] = Field(default_factory=tuple)
    missing_data_policy: MissingDataPolicy


class NumericSummary(FrozenPolarisBaseModel):
    count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    mean: float | None = None
    standard_deviation: float | None = None
    minimum: float | None = None
    percentile_25: float | None = None
    median: float | None = None
    percentile_75: float | None = None
    maximum: float | None = None


class CategoricalSummary(FrozenPolarisBaseModel):
    count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    unique_count: int = Field(ge=0)
    most_frequent_value: str | bool | None = None
    most_frequent_value_count: int = Field(ge=0)


class DescriptiveVariableSummary(FrozenPolarisBaseModel):
    variable_id: VariableId
    variable_type: str
    numeric: NumericSummary | None = None
    categorical: CategoricalSummary | None = None
    findings: tuple[AnalysisFinding, ...] = Field(default_factory=tuple)


class DescriptiveAnalysisResult(FrozenPolarisBaseModel):
    result_type: Literal["descriptive"] = "descriptive"
    variables: tuple[DescriptiveVariableSummary, ...]


class CorrelationPairResult(FrozenPolarisBaseModel):
    variable_id_1: VariableId
    variable_id_2: VariableId
    method: Literal["pearson", "spearman"]
    observation_count: int = Field(ge=0)
    correlation_coefficient: float | None = None
    p_value: float | None = None
    defined: bool
    warnings: tuple[AnalysisFinding, ...] = Field(default_factory=tuple)
    excluded_row_numbers: tuple[int, ...] = Field(default_factory=tuple)


class CorrelationAnalysisResult(FrozenPolarisBaseModel):
    result_type: Literal["correlation"] = "correlation"
    method: Literal["pearson", "spearman"]
    pairs: tuple[CorrelationPairResult, ...]


class RegressionCoefficient(FrozenPolarisBaseModel):
    term: str
    variable_id: VariableId | None = None
    estimate: float | None
    standard_error: float | None
    test_statistic: float | None
    p_value: float | None
    confidence_interval_low: float | None
    confidence_interval_high: float | None
    below_significance_threshold: bool | None = None
    standard_error_type: str | None = None
    cluster_count: int | None = Field(default=None, ge=0)


class RegressionSummary(FrozenPolarisBaseModel):
    count: int = Field(ge=0)
    mean: float | None
    standard_deviation: float | None
    minimum: float | None
    maximum: float | None


class DiagnosticResult(FrozenPolarisBaseModel):
    name: NonEmptyStr
    status: DiagnosticStatus
    statistic: float | None = None
    p_value: float | None = None
    variable_id: VariableId | None = None
    warning_codes: tuple[AnalysisFindingCode, ...] = Field(default_factory=tuple)
    explanation: NonEmptyStr


class OLSRegressionResult(FrozenPolarisBaseModel):
    result_type: Literal["ols_regression"] = "ols_regression"
    dependent_variable_id: VariableId
    predictor_variable_ids: tuple[VariableId, ...]
    sample_size: int = Field(ge=0)
    coefficients: tuple[RegressionCoefficient, ...]
    include_intercept: bool
    r_squared: float | None
    adjusted_r_squared: float | None
    residual_degrees_of_freedom: float
    model_degrees_of_freedom: float
    residual_sum_of_squares: float | None
    mean_squared_error: float | None
    fitted_value_summary: RegressionSummary
    residual_summary: RegressionSummary
    warnings: tuple[AnalysisFinding, ...] = Field(default_factory=tuple)


class PanelFixedEffectsConfig(FrozenPolarisBaseModel):
    entity_variable_id: VariableId
    time_variable_id: VariableId
    entity_fixed_effects: bool
    time_fixed_effects: bool
    intercept_reported: bool = False
    intercept_explanation: NonEmptyStr


class PanelClusterConfig(FrozenPolarisBaseModel):
    strategy: NonEmptyStr
    cluster_variable_id: VariableId | None = None
    cluster_count: int = Field(ge=0)
    warning: NonEmptyStr | None = None


class PanelLagOperation(FrozenPolarisBaseModel):
    source_variable_id: VariableId
    generated_variable_id: VariableId
    lag_periods: int = Field(gt=0)
    require_consecutive_time: bool = True
    rows_lost: int = Field(ge=0)
    excluded_row_numbers: tuple[int, ...] = Field(default_factory=tuple)
    missing_lag_reasons: tuple[tuple[int, NonEmptyStr], ...] = Field(default_factory=tuple)


class PanelSampleSummary(FrozenPolarisBaseModel):
    input_rows: int = Field(ge=0)
    included_rows: int = Field(ge=0)
    excluded_rows: int = Field(ge=0)
    entity_count: int = Field(ge=0)
    time_period_count: int = Field(ge=0)
    min_observations_per_entity: int | None = Field(default=None, ge=0)
    max_observations_per_entity: int | None = Field(default=None, ge=0)
    balanced: bool
    year_range: tuple[int | float, int | float] | None = None
    lag_induced_exclusions: int = Field(ge=0)
    missing_data_exclusions: int = Field(ge=0)
    singleton_entity_exclusions: int = Field(ge=0)
    cluster_count: int = Field(ge=0)
    effective_model_sample: int = Field(ge=0)


class PanelVariableVariation(FrozenPolarisBaseModel):
    variable_id: VariableId
    overall_mean: float | None = None
    overall_standard_deviation: float | None = None
    within_entity_standard_deviation: float | None = None
    between_entity_standard_deviation: float | None = None
    low_within_variation: bool = False


class PanelFitMetrics(FrozenPolarisBaseModel):
    within_r_squared: float | None = None
    between_r_squared: float | None = None
    overall_r_squared: float | None = None
    adjusted_within_r_squared: float | None = None


class PanelRegressionResult(FrozenPolarisBaseModel):
    result_type: Literal["panel_regression"] = "panel_regression"
    procedure: StatisticalProcedure
    dependent_variable_id: VariableId
    predictor_variable_ids: tuple[VariableId, ...]
    sample_size: int = Field(ge=0)
    coefficients: tuple[RegressionCoefficient, ...]
    fixed_effects: PanelFixedEffectsConfig
    cluster: PanelClusterConfig
    panel_sample: PanelSampleSummary
    lag_operations: tuple[PanelLagOperation, ...] = Field(default_factory=tuple)
    variation: tuple[PanelVariableVariation, ...] = Field(default_factory=tuple)
    fit: PanelFitMetrics
    residual_degrees_of_freedom: float
    model_degrees_of_freedom: float
    residual_sum_of_squares: float | None
    mean_squared_error: float | None
    fitted_value_summary: RegressionSummary
    residual_summary: RegressionSummary
    transformed_condition_number: float | None = None
    warnings: tuple[AnalysisFinding, ...] = Field(default_factory=tuple)


class AnalysisProvenance(FrozenPolarisBaseModel):
    dataset_id: DatasetId
    source_checksum_sha256: str
    ingestion_timestamp: AwareDatetime
    specification: StatisticalSpecification
    included_row_numbers: tuple[int, ...]
    excluded_row_numbers: tuple[int, ...]
    analysis_timestamp: AwareDatetime
    library_versions: tuple[str, ...]
    software_version: NonEmptyStr
    schema_version: SchemaVersion = ANALYSIS_SCHEMA_VERSION
    execution_settings: AnalysisExecutionSettings


class AnalysisResult(FrozenPolarisBaseModel):
    result_id: NonEmptyStr
    analysis_method: StatisticalProcedure
    statistical_specification: StatisticalSpecification
    dataset_id: DatasetId
    source_checksum_sha256: str
    analysis_sample: AnalysisSampleSummary
    method_result: (
        DescriptiveAnalysisResult
        | CorrelationAnalysisResult
        | OLSRegressionResult
        | PanelRegressionResult
    )
    diagnostics: tuple[DiagnosticResult, ...] = Field(default_factory=tuple)
    findings: tuple[AnalysisFinding, ...] = Field(default_factory=tuple)
    analysis_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    software_version: NonEmptyStr
    schema_version: SchemaVersion = ANALYSIS_SCHEMA_VERSION
    provenance: AnalysisProvenance
    provenance_record: ProvenanceRecord | None = None
