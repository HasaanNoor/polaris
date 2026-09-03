"""Typed contracts for Phase 25 visualization artifacts."""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator, model_validator

from polaris.schemas.common import FrozenPolarisBaseModel, NonEmptyStr, SchemaVersion, VariableId

VISUALIZATION_SCHEMA_VERSION = "1.0.0"
VISUALIZATION_RULESET_VERSION = "research_visualization_phase25_v1"
MAX_DEFAULT_ENTITIES = 8
MAX_CORRELATION_VARIABLES = 12


class VisualizationType(StrEnum):
    COUNTRY_TIME_SERIES = "country_time_series"
    MULTI_COUNTRY_TREND = "multi_country_trend"
    SCATTERPLOT = "scatterplot"
    REGRESSION_RELATIONSHIP = "regression_relationship"
    COEFFICIENT_PLOT = "coefficient_plot"
    MODEL_COMPARISON = "model_comparison"
    EVENT_STUDY = "event_study"
    CAUSAL_ESTIMATE = "causal_estimate"
    ROBUSTNESS_ESTIMATES = "robustness_estimates"
    LEAVE_ONE_OUT = "leave_one_out"
    PLACEBO = "placebo"
    CORRELATION_MATRIX = "correlation_matrix"
    MISSINGNESS_BY_VARIABLE = "missingness_by_variable"
    MISSINGNESS_BY_YEAR = "missingness_by_year"
    MISSINGNESS_BY_ENTITY = "missingness_by_entity"
    COUNTRY_YEAR_COVERAGE = "country_year_coverage"
    DISTRIBUTION_HISTOGRAM = "distribution_histogram"
    DISTRIBUTION_BOX = "distribution_box"
    PANEL_DIAGNOSTIC = "panel_diagnostic"
    CAUSAL_STUDY_DIAGNOSTIC = "causal_study_diagnostic"


class OutputFormat(StrEnum):
    PNG = "png"
    SVG = "svg"
    CSV = "csv"
    JSON = "json"


class ReferenceLineOrientation(StrEnum):
    X = "x"
    Y = "y"


class AxisScale(StrEnum):
    LINEAR = "linear"
    LOG = "log"


class PanelDiagnosticKind(StrEnum):
    OBSERVATIONS_BY_ENTITY = "observations_by_entity"
    TIME_COVERAGE = "time_coverage"
    WITHIN_BETWEEN_VARIATION = "within_between_variation"


class ReferenceLine(FrozenPolarisBaseModel):
    orientation: ReferenceLineOrientation
    value: int | float
    label: NonEmptyStr | None = None


class AxisMetadata(FrozenPolarisBaseModel):
    variable_id: VariableId | None = None
    label: NonEmptyStr
    unit: NonEmptyStr | None = None
    scale: AxisScale = AxisScale.LINEAR
    truncated: bool = False
    lower_bound: float | None = None
    upper_bound: float | None = None

    @model_validator(mode="after")
    def require_explicit_truncation_bounds(self) -> AxisMetadata:
        if self.truncated and self.lower_bound is None and self.upper_bound is None:
            raise ValueError("truncated axes require an explicit bound")
        return self


class LegendEntry(FrozenPolarisBaseModel):
    key: NonEmptyStr
    label: NonEmptyStr
    style: NonEmptyStr | None = None


class Annotation(FrozenPolarisBaseModel):
    text: NonEmptyStr
    x: int | float | str | None = None
    y: int | float | str | None = None
    category: NonEmptyStr = "methodological_note"


class OutputReference(FrozenPolarisBaseModel):
    format: OutputFormat
    path: NonEmptyStr
    checksum_sha256: str | None = None
    bytes: int | None = Field(default=None, ge=0)


class VisualizationSpecification(FrozenPolarisBaseModel):
    visualization_type: VisualizationType
    source_artifact_id: NonEmptyStr
    title: NonEmptyStr | None = None
    subtitle: NonEmptyStr | None = None
    x_variable: VariableId | None = None
    y_variable: VariableId | None = None
    grouping_variable: VariableId | None = None
    entity_variable: VariableId | None = None
    time_variable: VariableId | None = None
    selected_entities: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    time_range: tuple[int | float, int | float] | None = None
    selected_variables: tuple[VariableId, ...] = Field(default_factory=tuple)
    selected_terms: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    selected_model_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    estimand_variable: VariableId | None = None
    include_confidence_interval: bool = True
    reference_lines: tuple[ReferenceLine, ...] = Field(default_factory=tuple)
    labels: dict[str, str] = Field(default_factory=dict)
    units: dict[str, str] = Field(default_factory=dict)
    output_formats: tuple[OutputFormat, ...] = (OutputFormat.PNG, OutputFormat.SVG)
    width: int = Field(default=960, ge=320, le=2400)
    height: int = Field(default=640, ge=240, le=1800)
    allow_many_entities: bool = False
    max_entities: int = Field(default=MAX_DEFAULT_ENTITIES, ge=1, le=50)
    panel_diagnostic: PanelDiagnosticKind | None = None
    axis_truncation_allowed: bool = False
    schema_version: SchemaVersion = VISUALIZATION_SCHEMA_VERSION
    ruleset_version: NonEmptyStr = VISUALIZATION_RULESET_VERSION

    @field_validator(
        "selected_entities",
        "selected_variables",
        "selected_terms",
        "selected_model_ids",
    )
    @classmethod
    def unique_sorted(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("output_formats")
    @classmethod
    def unique_output_formats(cls, value: tuple[OutputFormat, ...]) -> tuple[OutputFormat, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @model_validator(mode="after")
    def validate_shape(self) -> VisualizationSpecification:
        if self.time_range is not None and self.time_range[0] > self.time_range[1]:
            raise ValueError("time_range must be ordered")
        if (
            self.visualization_type
            in {VisualizationType.COUNTRY_TIME_SERIES, VisualizationType.MULTI_COUNTRY_TREND}
            and not self.selected_entities
        ):
            raise ValueError("country trend visualizations require selected_entities")
        if len(self.selected_entities) > self.max_entities and not self.allow_many_entities:
            raise ValueError("selected_entities exceeds max_entities without explicit override")
        if (
            self.visualization_type is VisualizationType.CORRELATION_MATRIX
            and len(self.selected_variables) > MAX_CORRELATION_VARIABLES
        ):
            raise ValueError("correlation matrix exceeds the deterministic variable limit")
        return self


class VisualizationArtifact(FrozenPolarisBaseModel):
    visualization_id: NonEmptyStr
    visualization_type: VisualizationType
    source_artifact_ids: tuple[NonEmptyStr, ...]
    specification: VisualizationSpecification
    plotting_data: tuple[dict[str, Any], ...]
    axis_metadata: dict[str, AxisMetadata] = Field(default_factory=dict)
    legend: tuple[LegendEntry, ...] = Field(default_factory=tuple)
    annotations: tuple[Annotation, ...] = Field(default_factory=tuple)
    limitations: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    warnings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    provenance: dict[str, Any] = Field(default_factory=dict)
    output_references: tuple[OutputReference, ...] = Field(default_factory=tuple)
    schema_version: SchemaVersion = VISUALIZATION_SCHEMA_VERSION
    ruleset_version: NonEmptyStr = VISUALIZATION_RULESET_VERSION

    @field_validator("source_artifact_ids")
    @classmethod
    def sort_source_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    def with_outputs(self, outputs: tuple[OutputReference, ...]) -> VisualizationArtifact:
        return self.model_copy(update={"output_references": outputs})


def deterministic_visualization_id(
    *,
    source_artifact_ids: tuple[str, ...],
    source_provenance: dict[str, Any],
    specification: VisualizationSpecification,
    schema_version: str = VISUALIZATION_SCHEMA_VERSION,
    ruleset_version: str = VISUALIZATION_RULESET_VERSION,
) -> str:
    payload = {
        "source_artifact_ids": sorted(set(source_artifact_ids)),
        "source_provenance": _json_ready(source_provenance),
        "specification": specification.model_dump(mode="json"),
        "schema_version": schema_version,
        "ruleset_version": ruleset_version,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "viz_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
