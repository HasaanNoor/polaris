"""Typed contracts for UNESCO UIS education panel integration."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import Field

from polaris.schemas.common import FrozenPolarisBaseModel, NonEmptyStr, SchemaVersion

UNESCO_PANEL_SCHEMA_VERSION = "1.0.0"
UNESCO_RULESET_VERSION = "2026-08-12"


class UNESCOEducationSuitability(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class UNESCOMissingnessReasonCode(StrEnum):
    SOURCE_VALUE_MISSING = "unesco_source_missing_value"
    COUNTRY_YEAR_ABSENT = "country_year_absent"
    AGGREGATE_ROW_EXCLUDED = "aggregate_row_excluded"
    TERRITORY_ROW_EXCLUDED = "territory_row_excluded"
    UNKNOWN_ENTITY_EXCLUDED = "unknown_entity_excluded"
    SEX_SPECIFIC_ROW_EXCLUDED = "sex_specific_row_excluded"
    SUBGROUP_ROW_EXCLUDED = "subgroup_row_excluded"
    DUPLICATE_UNRESOLVED = "duplicate_unresolved"
    INCOMPATIBLE_SCHEMA = "incompatible_schema"
    DEFERRED_INDICATOR = "deferred_indicator"


class UNESCODimensionFilter(FrozenPolarisBaseModel):
    field: NonEmptyStr
    allowed_values: tuple[str | None, ...]
    reason: NonEmptyStr


class UNESCOIndicatorProfile(FrozenPolarisBaseModel):
    source_dataset: NonEmptyStr
    source_file: NonEmptyStr
    source_checksum: NonEmptyStr
    unesco_indicator_id: NonEmptyStr
    official_title: NonEmptyStr
    definition: NonEmptyStr | None = None
    country_field: NonEmptyStr | None = "COUNTRY_ID"
    iso_code_field: NonEmptyStr | None = "COUNTRY_ID"
    year_field: NonEmptyStr | None = "YEAR"
    numeric_value_field: NonEmptyStr | None = "VALUE"
    unit: NonEmptyStr | None = None
    sex_dimension: NonEmptyStr | None = None
    age_dimension: NonEmptyStr | None = None
    education_level_dimension: NonEmptyStr | None = None
    location_dimension: NonEmptyStr | None = None
    wealth_dimension: NonEmptyStr | None = None
    estimate_status_dimension: NonEmptyStr | None = None
    country_coverage: int = Field(ge=0)
    temporal_coverage: tuple[int, int] | None = None
    row_count: int = Field(ge=0)
    missing_value_count: int = Field(ge=0)
    duplicate_key_findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    aggregate_record_count: int = Field(ge=0)
    suitability_classification: UNESCOEducationSuitability
    schema_findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class UNESCOEducationVariableMapping(FrozenPolarisBaseModel):
    unesco_indicator_id: NonEmptyStr
    official_title: NonEmptyStr
    canonical_variable_id: NonEmptyStr
    canonical_label: NonEmptyStr
    definition: NonEmptyStr
    unit: NonEmptyStr
    source_dataset: NonEmptyStr = "SDG"
    source_field: NonEmptyStr = "VALUE"
    country_field: NonEmptyStr = "COUNTRY_ID"
    year_field: NonEmptyStr = "YEAR"
    required_filters: tuple[UNESCODimensionFilter, ...] = Field(default_factory=tuple)
    allowed_sex_category: NonEmptyStr | None = "both sexes"
    allowed_education_level: NonEmptyStr | None = None
    allowed_age_group: NonEmptyStr | None = None
    allowed_location_category: NonEmptyStr | None = None
    modeled_estimates_accepted: bool = False
    notes: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    ruleset_version: NonEmptyStr = UNESCO_RULESET_VERSION


class UNESCOValueProvenance(FrozenPolarisBaseModel):
    canonical_variable_id: NonEmptyStr
    unesco_indicator_id: NonEmptyStr
    official_title: NonEmptyStr
    source_dataset: NonEmptyStr
    source_file: NonEmptyStr
    source_checksum: NonEmptyStr
    source_row: int = Field(ge=1)
    original_country_identifier: NonEmptyStr
    original_year: int
    original_value: str | int | float | None
    normalized_value: float
    unit: NonEmptyStr
    sex: NonEmptyStr | None = None
    age_cohort: NonEmptyStr | None = None
    education_level: NonEmptyStr | None = None
    location_dimension: NonEmptyStr | None = None
    estimate_status: NonEmptyStr | None = None
    applied_filters: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    source_manifest_reference: NonEmptyStr
    ruleset_version: NonEmptyStr = UNESCO_RULESET_VERSION


class UNESCOEducationRecord(FrozenPolarisBaseModel):
    canonical_country_code: NonEmptyStr
    canonical_country_name: NonEmptyStr
    year: int
    values: dict[str, float] = Field(default_factory=dict)
    value_provenance: dict[str, UNESCOValueProvenance] = Field(default_factory=dict)
    contributing_unesco_indicators: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    schema_version: SchemaVersion = UNESCO_PANEL_SCHEMA_VERSION


class UNESCODeferredIndicator(FrozenPolarisBaseModel):
    source_dataset: NonEmptyStr
    unesco_indicator_id: NonEmptyStr
    title: NonEmptyStr
    suitability: UNESCOEducationSuitability
    reason_deferred: NonEmptyStr
    problematic_dimensions: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    coverage_issue: NonEmptyStr | None = None
    future_work_needed: NonEmptyStr
    potential_analytical_use: NonEmptyStr | None = None


class UNESCOEducationQualitySummary(FrozenPolarisBaseModel):
    candidate_indicator_count: int = Field(ge=0)
    integrated_indicator_count: int = Field(ge=0)
    deferred_indicator_count: int = Field(ge=0)
    country_count: int = Field(ge=0)
    year_range: tuple[int, int] | None = None
    country_year_record_count: int = Field(ge=0)
    missingness_by_variable: dict[str, dict[str, int]] = Field(default_factory=dict)
    aggregate_exclusions: int = Field(ge=0)
    sex_specific_exclusions: int = Field(ge=0)
    subgroup_exclusions: int = Field(ge=0)
    territory_exclusions: int = Field(ge=0)
    unknown_entity_exclusions: int = Field(ge=0)
    duplicate_findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    source_coverage: dict[str, int] = Field(default_factory=dict)
    analysis_ready: bool


class UNESCOEducationPanel(FrozenPolarisBaseModel):
    panel_id: NonEmptyStr
    integrated_variable_catalog: tuple[UNESCOEducationVariableMapping, ...]
    records: tuple[UNESCOEducationRecord, ...]
    value_provenance: tuple[UNESCOValueProvenance, ...]
    indicator_profiles: tuple[UNESCOIndicatorProfile, ...]
    quality_summary: UNESCOEducationQualitySummary
    findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    deferred_indicator_registry: tuple[UNESCODeferredIndicator, ...]
    source_checksums: dict[str, str]
    ruleset_version: NonEmptyStr = UNESCO_RULESET_VERSION
    schema_version: SchemaVersion = UNESCO_PANEL_SCHEMA_VERSION
    creation_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UNESCOEducationPanelExportResult(FrozenPolarisBaseModel):
    csv_path: Path
    manifest_path: Path
    quality_summary_path: Path
    variable_catalog_path: Path
    deferred_indicators_path: Path
    provenance_path: Path | None = None
    dataset_id: NonEmptyStr
    checksum_sha256: NonEmptyStr


def json_ready(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude={"creation_timestamp"})
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    return value
