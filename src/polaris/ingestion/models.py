"""Typed contracts for local tabular dataset ingestion."""

from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator, model_validator

from polaris.schemas.common import (
    AwareDatetime,
    DatasetId,
    FrozenPolarisBaseModel,
    NonEmptyStr,
    SchemaVersion,
    VariableId,
)
from polaris.schemas.dataset import DatasetManifest
from polaris.schemas.provenance import ProvenanceRecord

SHA256_PATTERN = r"^[a-fA-F0-9]{64}$"


class UnexpectedColumnMode(StrEnum):
    """How ingestion handles source columns absent from a manifest."""

    STRICT = "strict"
    PERMISSIVE = "permissive"


class ValidationSeverity(StrEnum):
    """Stable severity levels for ingestion findings."""

    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationFindingCode(StrEnum):
    """Machine-readable ingestion finding codes."""

    EMPTY_DATASET = "empty_dataset"
    MISSING_REQUIRED_COLUMN = "missing_required_column"
    UNEXPECTED_COLUMN = "unexpected_column"
    DUPLICATE_COLUMN = "duplicate_column"
    MALFORMED_ROW = "malformed_row"
    INVALID_VALUE_TYPE = "invalid_value_type"
    MISSING_VALUE = "missing_value"
    UNMAPPED_VARIABLE = "unmapped_variable"
    AMBIGUOUS_COLUMN_MAPPING = "ambiguous_column_mapping"
    INVALID_MANIFEST_DECLARATION = "invalid_manifest_declaration"


class IngestionConfiguration(FrozenPolarisBaseModel):
    """Options intentionally limited to deterministic local CSV ingestion."""

    delimiter: str = ","
    encoding: NonEmptyStr = "utf-8"
    header: bool = True
    null_value_tokens: tuple[str, ...] = ("", "null", "NULL", "NA", "N/A")
    unexpected_column_mode: UnexpectedColumnMode = UnexpectedColumnMode.STRICT
    allow_type_coercion: bool = True
    max_validation_error_samples: int = Field(default=50, ge=0)
    require_source_checksum: bool = False

    @field_validator("delimiter")
    @classmethod
    def validate_delimiter(cls, value: str) -> str:
        if len(value) != 1:
            raise ValueError("delimiter must be a single character")
        if value in {"\n", "\r", '"'}:
            raise ValueError("delimiter must not be a newline or quote character")
        return value

    @model_validator(mode="after")
    def require_header(self) -> "IngestionConfiguration":
        if not self.header:
            raise ValueError("Phase 3 ingestion requires a header row")
        return self


class IngestionRequest(FrozenPolarisBaseModel):
    """Request to ingest a local source file for a registered manifest."""

    dataset_id: DatasetId
    source_path: Path
    configuration: IngestionConfiguration = Field(default_factory=IngestionConfiguration)
    expected_checksum: str | None = Field(default=None, pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def require_checksum_when_configured(self) -> "IngestionRequest":
        if self.configuration.require_source_checksum and self.expected_checksum is None:
            raise ValueError("expected_checksum is required when require_source_checksum is true")
        return self


class SourceFileMetadata(FrozenPolarisBaseModel):
    """Content-identity metadata for an ingested local source file."""

    source_path: str
    checksum_sha256: str = Field(pattern=SHA256_PATTERN)
    file_size_bytes: int = Field(ge=0)


class RawTabularRow(FrozenPolarisBaseModel):
    """One parsed source row with source row order and line number retained."""

    row_number: int
    line_number: int
    values: tuple[str, ...]


class LoadedTabularFile(FrozenPolarisBaseModel):
    """CSV loading output before manifest mapping or type normalization."""

    source_path: str
    source_columns: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[RawTabularRow, ...] = Field(default_factory=tuple)
    malformed_rows: tuple[RawTabularRow, ...] = Field(default_factory=tuple)
    parse_succeeded: bool = True


class ColumnMapping(FrozenPolarisBaseModel):
    """Exact mapping from a source column to a manifest variable."""

    variable_id: VariableId
    source_column: str
    source_index: int


class ValidationFinding(FrozenPolarisBaseModel):
    """Typed validation finding with stable codes and source context."""

    severity: ValidationSeverity
    code: ValidationFindingCode
    message: NonEmptyStr
    source_path: str | None = None
    row_number: int | None = None
    source_column: str | None = None
    variable_id: VariableId | None = None
    raw_value: str | None = None


class NormalizedRecord(FrozenPolarisBaseModel):
    """Analysis-ready source row with values keyed by canonical variable id."""

    row_number: int
    source_line_number: int
    values: dict[str, str | int | float | bool | date | datetime | None]
    source_columns: dict[str, str]


class StructuralValidationReport(FrozenPolarisBaseModel):
    """Summary of parsing, manifest-column validation, and row acceptance."""

    source_path: str
    dataset_id: DatasetId
    source_row_count: int
    accepted_row_count: int
    rejected_row_count: int
    source_columns: tuple[str, ...] = Field(default_factory=tuple)
    mapped_columns: tuple[ColumnMapping, ...] = Field(default_factory=tuple)
    missing_columns: tuple[str, ...] = Field(default_factory=tuple)
    unexpected_columns: tuple[str, ...] = Field(default_factory=tuple)
    validation_findings: tuple[ValidationFinding, ...] = Field(default_factory=tuple)
    parsing_succeeded: bool
    validation_succeeded: bool
    analysis_ready: bool


class VariableQualityProfile(FrozenPolarisBaseModel):
    """Deterministic structural profile for one mapped variable."""

    variable_id: VariableId
    source_column: str
    data_type: str
    non_null_count: int = Field(ge=0)
    null_count: int = Field(ge=0)
    invalid_value_count: int = Field(ge=0)
    unique_value_count: int = Field(ge=0)
    minimum: int | float | str | None = None
    maximum: int | float | str | None = None
    observed_types: tuple[str, ...] = Field(default_factory=tuple)


class DataQualityProfile(FrozenPolarisBaseModel):
    """Deterministic structural and data-quality summary."""

    dataset_id: DatasetId
    row_count: int = Field(ge=0)
    accepted_row_count: int = Field(ge=0)
    rejected_row_count: int = Field(ge=0)
    duplicate_record_count: int = Field(ge=0)
    variables: tuple[VariableQualityProfile, ...] = Field(default_factory=tuple)


class IngestionProvenance(FrozenPolarisBaseModel):
    """Ingestion-specific provenance metadata for a local file read."""

    dataset_id: DatasetId
    source_path: str
    checksum_sha256: str = Field(pattern=SHA256_PATTERN)
    file_size_bytes: int = Field(ge=0)
    ingestion_timestamp: AwareDatetime
    configuration: IngestionConfiguration
    software_version: NonEmptyStr | None = None
    schema_version: SchemaVersion = "1.0.0"


class DatasetIngestionResult(FrozenPolarisBaseModel):
    """Immutable result for successful local tabular ingestion."""

    dataset_manifest: DatasetManifest
    ingestion_request: IngestionRequest
    source_metadata: SourceFileMetadata
    checksum_sha256: str = Field(pattern=SHA256_PATTERN)
    normalized_records: tuple[NormalizedRecord, ...] = Field(default_factory=tuple)
    validation_report: StructuralValidationReport
    quality_profile: DataQualityProfile
    provenance: IngestionProvenance
    provenance_record: ProvenanceRecord | None = None
    ingestion_timestamp: AwareDatetime
    schema_version: SchemaVersion = "1.0.0"


NormalizedValue = str | int | float | bool | date | datetime | None
RawRecord = dict[str, Any]
