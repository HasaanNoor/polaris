"""Typed contracts for cross-dataset country-year harmonization."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, computed_field, model_validator

from polaris.ingestion.models import DatasetIngestionResult, NormalizedValue
from polaris.schemas.common import (
    DatasetId,
    FrozenPolarisBaseModel,
    GeographicScope,
    NonEmptyStr,
    SchemaVersion,
    TemporalScope,
)

HARMONIZATION_SCHEMA_VERSION = "1.0.0"
HARMONIZATION_RULESET_VERSION = "2026-08-06"


class JoinType(StrEnum):
    INNER = "inner"
    LEFT = "left"
    FULL_OUTER = "full_outer"


class DuplicateKeyBehavior(StrEnum):
    REJECT = "reject"
    PRESERVE_CONFLICT = "preserve_conflict"


class TransformationRule(StrEnum):
    NONE = "none"
    RENAME_ONLY = "rename_only"
    PERCENT_TO_PROPORTION = "percent_to_proportion"
    PROPORTION_TO_PERCENT = "proportion_to_percent"


class CompatibilityStatus(StrEnum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    DEFERRED = "deferred"


class GeographicEntityType(StrEnum):
    SOVEREIGN_COUNTRY = "sovereign_country"
    TERRITORY = "territory"
    REGION = "region"
    INCOME_GROUP = "income_group"
    GLOBAL_AGGREGATE = "global_aggregate"
    UNKNOWN = "unknown"


class HarmonizationSeverity(StrEnum):
    FATAL = "fatal"
    WARNING = "warning"
    INFO = "info"


class HarmonizationFindingCode(StrEnum):
    UNMAPPED_COUNTRY = "UNMAPPED_COUNTRY"
    AGGREGATE_ENTITY_EXCLUDED = "AGGREGATE_ENTITY_EXCLUDED"
    TERRITORY_EXCLUDED = "TERRITORY_EXCLUDED"
    INVALID_YEAR = "INVALID_YEAR"
    NON_ANNUAL_PERIOD_UNSUPPORTED = "NON_ANNUAL_PERIOD_UNSUPPORTED"
    VARIABLE_NOT_FOUND = "VARIABLE_NOT_FOUND"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    DEFINITION_MISMATCH = "DEFINITION_MISMATCH"
    DUPLICATE_COUNTRY_YEAR = "DUPLICATE_COUNTRY_YEAR"
    CONFLICTING_SOURCE_VALUES = "CONFLICTING_SOURCE_VALUES"
    JOIN_MISSING_VALUE = "JOIN_MISSING_VALUE"
    SOURCE_VALUE_MISSING = "SOURCE_VALUE_MISSING"
    TRANSFORMATION_APPLIED = "TRANSFORMATION_APPLIED"
    PROVIDER_PRECEDENCE_APPLIED = "PROVIDER_PRECEDENCE_APPLIED"
    DATASET_EXCLUDED = "DATASET_EXCLUDED"
    NO_COMPATIBLE_VARIABLES = "NO_COMPATIBLE_VARIABLES"


class MissingnessReasonCode(StrEnum):
    SOURCE_VALUE_MISSING = "source_value_missing"
    COUNTRY_YEAR_ABSENT = "country_year_absent"
    SOURCE_VARIABLE_UNAVAILABLE = "source_variable_unavailable"
    ROW_EXCLUDED_DURING_INGESTION = "row_excluded_during_ingestion"
    UNMAPPED_COUNTRY = "unmapped_country"
    UNMAPPED_YEAR = "unmapped_year"
    INCOMPATIBLE_UNIT = "incompatible_unit"
    UNRESOLVED_DUPLICATE = "unresolved_duplicate"
    JOIN_INDUCED_MISSING = "join_induced_missing"


class DatasetHarmonizationConfig(FrozenPolarisBaseModel):
    """Per-ingestion-result country and time declarations."""

    dataset_id: DatasetId
    alias: NonEmptyStr
    provider: NonEmptyStr
    country_field: NonEmptyStr
    year_field: NonEmptyStr
    country_name_field: NonEmptyStr | None = None
    geographic_level_field: NonEmptyStr | None = None
    include_aggregate_entities: bool = False


class VariableMapping(FrozenPolarisBaseModel):
    """Reviewed source-to-canonical variable mapping."""

    source_dataset_id: DatasetId
    source_provider: NonEmptyStr
    source_variable_id: NonEmptyStr
    source_field_name: NonEmptyStr
    canonical_variable_id: NonEmptyStr
    canonical_label: NonEmptyStr
    source_unit: NonEmptyStr | None = None
    canonical_unit: NonEmptyStr | None = None
    conceptual_definition: NonEmptyStr
    expected_data_type: NonEmptyStr
    aggregation_level: NonEmptyStr = "country-year"
    transformation_rule: TransformationRule = TransformationRule.RENAME_ONLY
    compatibility_status: CompatibilityStatus = CompatibilityStatus.COMPATIBLE
    row_filters: dict[str, str] = Field(default_factory=dict)
    notes: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class ProviderPrecedenceRule(FrozenPolarisBaseModel):
    canonical_variable_id: NonEmptyStr
    provider_order: tuple[NonEmptyStr, ...] = Field(min_length=2)


class HarmonizationStrictness(FrozenPolarisBaseModel):
    duplicate_key_behavior: DuplicateKeyBehavior = DuplicateKeyBehavior.REJECT
    exclude_aggregate_entities: bool = True
    exclude_territories: bool = False
    require_unit_match: bool = True
    require_definition: bool = True


class HarmonizationRequest(FrozenPolarisBaseModel):
    """Synchronous request to build one harmonized country-year artifact."""

    ingestion_results: tuple[DatasetIngestionResult, ...] = Field(min_length=2)
    dataset_configs: tuple[DatasetHarmonizationConfig, ...] = Field(min_length=2)
    variable_mappings: tuple[VariableMapping, ...] = Field(min_length=1)
    join_type: JoinType
    anchor_dataset_id: DatasetId | None = None
    geographic_scope: GeographicScope | None = None
    temporal_scope: TemporalScope | None = None
    provider_precedence: tuple[ProviderPrecedenceRule, ...] = Field(default_factory=tuple)
    strictness: HarmonizationStrictness = Field(default_factory=HarmonizationStrictness)
    output_dataset_id: DatasetId | None = None
    schema_version: SchemaVersion = HARMONIZATION_SCHEMA_VERSION
    ruleset_version: NonEmptyStr = HARMONIZATION_RULESET_VERSION

    @model_validator(mode="after")
    def validate_request_shape(self) -> HarmonizationRequest:
        result_ids = tuple(result.dataset_manifest.dataset_id for result in self.ingestion_results)
        config_ids = tuple(config.dataset_id for config in self.dataset_configs)
        if len(set(result_ids)) != len(result_ids):
            raise ValueError("ingestion result dataset IDs must be unique")
        if set(result_ids) != set(config_ids):
            raise ValueError("dataset configs must exactly match ingestion result dataset IDs")
        if self.join_type is JoinType.LEFT and self.anchor_dataset_id is None:
            raise ValueError("left join requires an explicit anchor_dataset_id")
        if self.anchor_dataset_id is not None and self.anchor_dataset_id not in result_ids:
            raise ValueError("anchor_dataset_id must identify an input dataset")
        for mapping in self.variable_mappings:
            if mapping.source_dataset_id not in result_ids:
                raise ValueError("variable mapping references an unknown source_dataset_id")
        return self


class NormalizedCountry(FrozenPolarisBaseModel):
    source_value: str
    canonical_code: str | None = None
    canonical_name: str | None = None
    entity_type: GeographicEntityType = GeographicEntityType.UNKNOWN
    provider: str | None = None
    finding: str | None = None

    @computed_field
    @property
    def country_level(self) -> bool:
        return self.entity_type in {
            GeographicEntityType.SOVEREIGN_COUNTRY,
            GeographicEntityType.TERRITORY,
        }


class HarmonizationFinding(FrozenPolarisBaseModel):
    severity: HarmonizationSeverity
    code: HarmonizationFindingCode
    message: NonEmptyStr
    dataset_id: DatasetId | None = None
    provider: NonEmptyStr | None = None
    canonical_variable_id: NonEmptyStr | None = None
    canonical_country_code: NonEmptyStr | None = None
    year: int | None = None
    source_row_number: int | None = None
    raw_value: str | None = None


class ValueProvenance(FrozenPolarisBaseModel):
    canonical_variable_id: NonEmptyStr
    source_dataset_id: DatasetId
    source_provider: NonEmptyStr
    source_checksum: NonEmptyStr
    source_variable_id: NonEmptyStr
    source_field_name: NonEmptyStr
    source_row_number: int
    source_line_number: int
    original_geographic_identifier: NonEmptyStr
    original_year_value: str | int
    original_raw_value: str | int | float | bool | None
    normalized_value: NormalizedValue
    transformation_applied: TransformationRule
    unit: NonEmptyStr | None = None
    retrieval_timestamp: datetime | None = None
    manifest_id: DatasetId
    source_path: NonEmptyStr


class HarmonizedRecord(FrozenPolarisBaseModel):
    canonical_country_code: NonEmptyStr
    canonical_country_name: NonEmptyStr
    year: int
    values: dict[str, NormalizedValue] = Field(default_factory=dict)
    value_provenance: dict[str, ValueProvenance] = Field(default_factory=dict)
    contributing_dataset_ids: tuple[DatasetId, ...] = Field(default_factory=tuple)
    source_row_references: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    missingness: dict[str, MissingnessReasonCode] = Field(default_factory=dict)
    findings: tuple[HarmonizationFinding, ...] = Field(default_factory=tuple)
    aggregate_entity: bool = False
    schema_version: SchemaVersion = HARMONIZATION_SCHEMA_VERSION


class VariableCatalogEntry(FrozenPolarisBaseModel):
    canonical_variable_id: NonEmptyStr
    canonical_label: NonEmptyStr
    provider: NonEmptyStr
    source_dataset_id: DatasetId
    source_variable_id: NonEmptyStr
    source_field_name: NonEmptyStr
    unit: NonEmptyStr | None = None
    conceptual_definition: NonEmptyStr
    transformation_rule: TransformationRule


class HarmonizationQualitySummary(FrozenPolarisBaseModel):
    input_dataset_count: int = Field(ge=0)
    input_accepted_record_counts: dict[str, int] = Field(default_factory=dict)
    output_country_year_record_count: int = Field(ge=0)
    countries_represented: tuple[str, ...] = Field(default_factory=tuple)
    years_represented: tuple[int, ...] = Field(default_factory=tuple)
    variables_represented: tuple[str, ...] = Field(default_factory=tuple)
    matched_country_count: int = Field(ge=0)
    unmapped_geographic_entities: dict[str, int] = Field(default_factory=dict)
    aggregate_entities_excluded: int = Field(ge=0)
    invalid_temporal_records: int = Field(ge=0)
    duplicate_keys: int = Field(ge=0)
    conflict_counts: dict[str, int] = Field(default_factory=dict)
    missingness_by_variable: dict[str, dict[str, int]] = Field(default_factory=dict)
    missingness_by_source: dict[str, dict[str, int]] = Field(default_factory=dict)
    join_coverage: dict[str, int] = Field(default_factory=dict)
    transformations_applied: dict[str, int] = Field(default_factory=dict)
    unresolved_issues: tuple[str, ...] = Field(default_factory=tuple)
    analysis_ready: bool


class DatasetHarmonizationProvenance(FrozenPolarisBaseModel):
    operation: NonEmptyStr = "country_year_harmonization"
    derived_artifact: bool = True
    input_dataset_ids: tuple[DatasetId, ...]
    source_checksums: dict[str, str]
    join_type: JoinType
    anchor_dataset_id: DatasetId | None = None
    ruleset_version: NonEmptyStr
    schema_version: SchemaVersion = HARMONIZATION_SCHEMA_VERSION
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HarmonizedDataset(FrozenPolarisBaseModel):
    harmonized_dataset_id: DatasetId
    request: HarmonizationRequest
    input_dataset_references: tuple[DatasetId, ...]
    canonical_variable_catalog: tuple[VariableCatalogEntry, ...]
    records: tuple[HarmonizedRecord, ...]
    quality_summary: HarmonizationQualitySummary
    findings: tuple[HarmonizationFinding, ...] = Field(default_factory=tuple)
    value_level_provenance: tuple[ValueProvenance, ...] = Field(default_factory=tuple)
    dataset_level_provenance: DatasetHarmonizationProvenance
    source_checksums: dict[str, str]
    creation_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    software_version: NonEmptyStr | None = None
    harmonization_schema_version: SchemaVersion = HARMONIZATION_SCHEMA_VERSION
    ruleset_version: NonEmptyStr = HARMONIZATION_RULESET_VERSION


def json_ready(value: Any) -> Any:
    """Return deterministic JSON-compatible data for hashing helpers."""

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude={"ingestion_results"})
    return value
