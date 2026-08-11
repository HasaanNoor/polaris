"""Typed contracts for World Bank WGI governance panel integration."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import Field

from polaris.schemas.common import AwareDatetime, FrozenPolarisBaseModel, NonEmptyStr, SchemaVersion

WGI_PANEL_SCHEMA_VERSION = "1.0.0"
WGI_RULESET_VERSION = "2026-08-11"
WGI_SOURCE_ID = "3"
WGI_SOURCE_CODE = "WGI"
WGI_SOURCE_LAST_UPDATED = "2026-03-18"
WGI_SOURCE_URL = "https://databank.worldbank.org/source/worldwide-governance-indicators"
WGI_API_URL = "https://api.worldbank.org/v2"


class WGIMissingnessReasonCode(StrEnum):
    SOURCE_VALUE_MISSING = "wgi_source_missing_value"
    COUNTRY_YEAR_ABSENT = "country_year_absent"
    AGGREGATE_ROW_EXCLUDED = "aggregate_row_excluded"
    TERRITORY_ROW_EXCLUDED = "territory_row_excluded"
    UNKNOWN_ENTITY_EXCLUDED = "unknown_entity_excluded"
    DUPLICATE_UNRESOLVED = "duplicate_unresolved"
    INCOMPATIBLE_SCHEMA = "incompatible_schema"


class WGIIndicatorRole(StrEnum):
    ESTIMATE = "estimate"
    STANDARD_ERROR = "standard_error"
    SOURCE_COUNT = "source_count"
    GOVERNANCE_SCORE = "governance_score"
    SCORE_LOWER_BOUND = "score_lower_bound"
    SCORE_UPPER_BOUND = "score_upper_bound"


class WGIVariableMapping(FrozenPolarisBaseModel):
    canonical_variable_id: NonEmptyStr
    canonical_label: NonEmptyStr
    official_dimension_code: NonEmptyStr
    official_estimate_indicator_id: NonEmptyStr
    official_title: NonEmptyStr
    definition: NonEmptyStr
    estimate_unit: NonEmptyStr
    estimate_scale: NonEmptyStr
    standard_error_indicator_id: NonEmptyStr
    source_count_indicator_id: NonEmptyStr
    governance_score_indicator_id: NonEmptyStr
    score_lower_bound_indicator_id: NonEmptyStr
    score_upper_bound_indicator_id: NonEmptyStr
    source_dataset: NonEmptyStr = "World Bank Worldwide Governance Indicators"
    source_url: NonEmptyStr = WGI_SOURCE_URL
    ruleset_version: NonEmptyStr = WGI_RULESET_VERSION


class WGISnapshotReference(FrozenPolarisBaseModel):
    provider: NonEmptyStr = "World Bank"
    dataset: NonEmptyStr = "Worldwide Governance Indicators"
    snapshot_path: Path
    metadata_path: Path | None = None
    source_url: NonEmptyStr
    checksum_sha256: NonEmptyStr
    original_filename: NonEmptyStr
    downloaded_at: AwareDatetime
    dimension_code: NonEmptyStr
    release: NonEmptyStr = "2025 Revision"
    license: NonEmptyStr = "Creative Commons Attribution 4.0"
    citation: NonEmptyStr = (
        "Worldwide Governance Indicators, 2025 Revision, World Bank (www.govindicators.org)."
    )


class WGIRow(FrozenPolarisBaseModel):
    source_path: NonEmptyStr
    source_checksum: NonEmptyStr
    source_row: int = Field(ge=1)
    data_source: NonEmptyStr
    last_updated_date: NonEmptyStr | None = None
    country_name: NonEmptyStr
    country_code: NonEmptyStr
    indicator_name: NonEmptyStr
    indicator_code: NonEmptyStr
    year: int
    value: float | None


class WGISchemaProfile(FrozenPolarisBaseModel):
    source_paths: tuple[NonEmptyStr, ...]
    source_checksums: dict[str, str]
    checksum_validated: bool
    row_count: int = Field(ge=0)
    country_identifier_field: NonEmptyStr | None = "Country Code"
    country_name_field: NonEmptyStr | None = "Country Name"
    year_field: NonEmptyStr | None = "Year"
    indicator_identifier_field: NonEmptyStr | None = "Indicator Code"
    indicator_title_field: NonEmptyStr | None = "Indicator Name"
    estimate_field: NonEmptyStr | None = "Value"
    standard_error_indicators: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    percentile_rank_indicators: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    confidence_bound_indicators: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    source_count_indicators: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    country_count: int = Field(ge=0)
    aggregate_count: int = Field(ge=0)
    territory_count: int = Field(ge=0)
    unknown_entity_count: int = Field(ge=0)
    year_range: tuple[int, int] | None = None
    missingness_by_indicator: dict[str, int] = Field(default_factory=dict)
    duplicate_key_findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    schema_findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class WGIValueProvenance(FrozenPolarisBaseModel):
    canonical_variable_id: NonEmptyStr
    official_wgi_indicator_id: NonEmptyStr
    official_title: NonEmptyStr
    source_dataset: NonEmptyStr
    source_snapshot: NonEmptyStr
    source_checksum: NonEmptyStr
    source_row: int = Field(ge=1)
    original_country_identifier: NonEmptyStr
    original_country_name: NonEmptyStr
    original_year: int
    original_estimate: float | None
    normalized_estimate: float
    standard_error: float | None = None
    governance_score: float | None = None
    score_lower_bound: float | None = None
    score_upper_bound: float | None = None
    percentile_rank: float | None = None
    number_of_sources: float | None = None
    retrieval_metadata: dict[str, str] = Field(default_factory=dict)
    mapping_ruleset_version: NonEmptyStr = WGI_RULESET_VERSION


class WGIGovernanceRecord(FrozenPolarisBaseModel):
    canonical_country_code: NonEmptyStr
    canonical_country_name: NonEmptyStr
    year: int
    values: dict[str, float] = Field(default_factory=dict)
    value_provenance: dict[str, WGIValueProvenance] = Field(default_factory=dict)
    uncertainty_metadata: dict[str, dict[str, float | None]] = Field(default_factory=dict)
    contributing_wgi_indicators: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    missingness: dict[str, WGIMissingnessReasonCode] = Field(default_factory=dict)
    findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    schema_version: SchemaVersion = WGI_PANEL_SCHEMA_VERSION


class WGIPanelQualitySummary(FrozenPolarisBaseModel):
    integrated_variable_count: int = Field(ge=0)
    country_count: int = Field(ge=0)
    year_range: tuple[int, int] | None = None
    country_year_record_count: int = Field(ge=0)
    missingness_by_variable: dict[str, dict[str, int]] = Field(default_factory=dict)
    aggregate_exclusions: int = Field(ge=0)
    territory_exclusions: int = Field(ge=0)
    unmapped_entities: dict[str, int] = Field(default_factory=dict)
    duplicate_keys: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    uncertainty_availability: dict[str, dict[str, int]] = Field(default_factory=dict)
    source_coverage: dict[str, int] = Field(default_factory=dict)
    analysis_ready: bool


class WGIGovernancePanel(FrozenPolarisBaseModel):
    panel_id: NonEmptyStr
    records: tuple[WGIGovernanceRecord, ...]
    variable_catalog: tuple[WGIVariableMapping, ...]
    source_checksums: dict[str, str]
    source_metadata: tuple[WGISnapshotReference, ...]
    schema_profile: WGISchemaProfile
    quality_summary: WGIPanelQualitySummary
    findings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    provenance: tuple[WGIValueProvenance, ...]
    ruleset_version: NonEmptyStr = WGI_RULESET_VERSION
    schema_version: SchemaVersion = WGI_PANEL_SCHEMA_VERSION
    creation_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))


class WGIPanelExportResult(FrozenPolarisBaseModel):
    csv_path: Path
    manifest_path: Path
    quality_summary_path: Path
    variable_catalog_path: Path
    provenance_path: Path | None = None
    dataset_id: NonEmptyStr
    checksum_sha256: NonEmptyStr


def json_ready(value: Any) -> Any:
    """Return deterministic JSON-compatible data for WGI hashing/export."""

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude={"creation_timestamp"})
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    return value
