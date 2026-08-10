"""Typed contracts for curated WHO GHO country-year panel integration."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import Field, model_validator

from polaris.schemas.common import FrozenPolarisBaseModel, NonEmptyStr, SchemaVersion

WHO_PANEL_SCHEMA_VERSION = "1.0.0"
WHO_RULESET_VERSION = "2026-08-10"


class WHOSuitability(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class WHOIntegrationStatus(StrEnum):
    INTEGRATED = "integrated"
    DEFERRED = "deferred"
    REJECTED = "rejected"


class WHOMissingnessReasonCode(StrEnum):
    SOURCE_VALUE_MISSING = "who_source_missing_value"
    COUNTRY_YEAR_ABSENT = "country_year_absent"
    INDICATOR_NOT_AVAILABLE = "indicator_not_available_for_country"
    ROW_EXCLUDED_BY_DIMENSION_RULE = "row_excluded_by_dimension_rule"
    PROJECTED_ROW_EXCLUDED = "projected_row_excluded"
    AGGREGATE_ROW_EXCLUDED = "aggregate_row_excluded"
    DUPLICATE_UNRESOLVED = "duplicate_unresolved"
    INCOMPATIBLE_SCHEMA = "incompatible_schema"
    DEFERRED_INDICATOR = "deferred_indicator"


class WHOIndicatorProfile(FrozenPolarisBaseModel):
    """Observed structure for one downloaded WHO GHO indicator snapshot."""

    who_indicator_id: NonEmptyStr
    official_title: NonEmptyStr
    conceptual_target: NonEmptyStr
    source_path: NonEmptyStr
    source_checksum: NonEmptyStr
    checksum_validated: bool
    row_count: int = Field(ge=0)
    geographic_field: NonEmptyStr | None = None
    temporal_field: NonEmptyStr | None = None
    numeric_value_fields: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    sex_dimensions: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    age_dimensions: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    estimate_status_dimensions: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    other_dimensions: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    units_observed: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    country_count: int = Field(ge=0)
    aggregate_count: int = Field(ge=0)
    territory_count: int = Field(ge=0)
    unknown_entity_count: int = Field(ge=0)
    year_range: tuple[int, int] | None = None
    null_counts: dict[str, int] = Field(default_factory=dict)
    duplicate_key_findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    schema_findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    suitability_classification: WHOSuitability


class WHODimensionRule(FrozenPolarisBaseModel):
    """Reviewed rule for selecting one country-year WHO concept."""

    field: NonEmptyStr
    allowed_values: tuple[str | None, ...]
    reason: NonEmptyStr
    exclude_reason_code: WHOMissingnessReasonCode = (
        WHOMissingnessReasonCode.ROW_EXCLUDED_BY_DIMENSION_RULE
    )


class WHOVariableMapping(FrozenPolarisBaseModel):
    """Reviewed mapping from a WHO indicator snapshot to one canonical variable."""

    who_indicator_id: NonEmptyStr
    canonical_variable_id: NonEmptyStr
    canonical_label: NonEmptyStr
    conceptual_definition: NonEmptyStr
    unit: NonEmptyStr
    preferred_numeric_source_field: NonEmptyStr = "NumericValue"
    country_field: NonEmptyStr = "SpatialDim"
    year_field: NonEmptyStr = "TimeDim"
    required_dimension_filters: tuple[WHODimensionRule, ...] = Field(default_factory=tuple)
    allowed_dimension_values: dict[str, tuple[str | None, ...]] = Field(default_factory=dict)
    modeled_estimates_accepted: bool = False
    projections_accepted: bool = False
    supported_year_range: tuple[int, int] | None = None
    integration_status: WHOIntegrationStatus = WHOIntegrationStatus.INTEGRATED
    notes: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    ruleset_version: NonEmptyStr = WHO_RULESET_VERSION

    @model_validator(mode="after")
    def mirror_allowed_dimension_values(self) -> WHOVariableMapping:
        rule_values = {rule.field: rule.allowed_values for rule in self.required_dimension_filters}
        if self.allowed_dimension_values and self.allowed_dimension_values != rule_values:
            raise ValueError("allowed_dimension_values must match required_dimension_filters")
        object.__setattr__(self, "allowed_dimension_values", rule_values)
        return self


class WHOValueProvenance(FrozenPolarisBaseModel):
    """Value-level provenance for one promoted WHO panel value."""

    who_indicator_id: NonEmptyStr
    official_title: NonEmptyStr
    canonical_variable_id: NonEmptyStr
    source_file: NonEmptyStr
    source_checksum: NonEmptyStr
    source_row: int = Field(ge=1)
    source_geographic_identifier: NonEmptyStr
    source_year: int
    source_value: str | int | float | None
    normalized_numeric_value: float
    unit: NonEmptyStr
    sex_dimension: str | None = None
    age_dimension: str | None = None
    estimate_model_dimension: str | None = None
    uncertainty_low: float | None = None
    uncertainty_high: float | None = None
    applied_filter_rules: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    retrieval_metadata_reference: NonEmptyStr | None = None
    acquisition_catalog_reference: NonEmptyStr
    ruleset_version: NonEmptyStr = WHO_RULESET_VERSION


class WHOHealthRecord(FrozenPolarisBaseModel):
    """Immutable country-year record with WHO values keyed by canonical variable id."""

    canonical_country_code: NonEmptyStr
    canonical_country_name: NonEmptyStr
    year: int
    values: dict[str, float] = Field(default_factory=dict)
    value_provenance: dict[str, WHOValueProvenance] = Field(default_factory=dict)
    contributing_indicator_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    missingness: dict[str, WHOMissingnessReasonCode] = Field(default_factory=dict)
    findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    schema_version: SchemaVersion = WHO_PANEL_SCHEMA_VERSION


class WHODeferredIndicator(FrozenPolarisBaseModel):
    """Machine-readable record for a WHO target not integrated into the panel."""

    who_indicator_id: str | None
    conceptual_target: NonEmptyStr
    suitability_classification: WHOSuitability | None = None
    reason_deferred: NonEmptyStr
    schema_issue: NonEmptyStr | None = None
    required_future_work: NonEmptyStr
    potentially_useful: bool


class WHOPanelQualitySummary(FrozenPolarisBaseModel):
    selected_indicator_count: int = Field(ge=0)
    integrated_indicator_count: int = Field(ge=0)
    deferred_indicator_count: int = Field(ge=0)
    country_count: int = Field(ge=0)
    year_range: tuple[int, int] | None = None
    country_year_record_count: int = Field(ge=0)
    aggregate_exclusions: int = Field(ge=0)
    territory_exclusions: int = Field(ge=0)
    unknown_entity_exclusions: int = Field(ge=0)
    missingness_by_variable: dict[str, dict[str, int]] = Field(default_factory=dict)
    variable_coverage: dict[str, int] = Field(default_factory=dict)
    duplicate_findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    modeled_series_count: int = Field(ge=0)
    projected_rows_excluded: int = Field(ge=0)
    sex_specific_rows_excluded: int = Field(ge=0)
    age_specific_rows_excluded: int = Field(ge=0)
    unresolved_schema_issues: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    analysis_ready: bool


class WHOHealthPanel(FrozenPolarisBaseModel):
    """Top-level deterministic WHO country-year health panel artifact."""

    panel_id: NonEmptyStr
    selected_indicator_definitions: tuple[WHOVariableMapping, ...]
    records: tuple[WHOHealthRecord, ...]
    value_provenance: tuple[WHOValueProvenance, ...]
    indicator_profiles: tuple[WHOIndicatorProfile, ...]
    quality_summary: WHOPanelQualitySummary
    findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    deferred_indicators: tuple[WHODeferredIndicator, ...]
    source_checksums: dict[str, str]
    ruleset_version: NonEmptyStr = WHO_RULESET_VERSION
    schema_version: SchemaVersion = WHO_PANEL_SCHEMA_VERSION
    creation_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WHOPanelExportResult(FrozenPolarisBaseModel):
    csv_path: Path
    manifest_path: Path
    quality_summary_path: Path
    variable_catalog_path: Path | None = None
    deferred_indicators_path: Path | None = None
    provenance_path: Path | None = None
    dataset_id: NonEmptyStr
    checksum_sha256: NonEmptyStr


def json_ready(value: Any) -> Any:
    """Return deterministic JSON-compatible data for WHO hashing/export."""

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude={"creation_timestamp"})
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    return value
