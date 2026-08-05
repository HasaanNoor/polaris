"""Typed contracts for Phase 11 real dataset validation."""

from pathlib import Path

from pydantic import Field

from polaris.reporting.models import GeneratedReport
from polaris.schemas.common import FrozenPolarisBaseModel, NonEmptyStr


class DiscoveredDataset(FrozenPolarisBaseModel):
    """One official dataset file discovered under data/raw."""

    provider: NonEmptyStr
    dataset_key: NonEmptyStr
    path: Path
    companion_files: tuple[Path, ...] = ()
    file_size_bytes: int = Field(ge=1)
    checksum_sha256: NonEmptyStr


class ColumnProfile(FrozenPolarisBaseModel):
    """Basic source-column profile from a bounded CSV inspection."""

    name: NonEmptyStr
    inferred_type: NonEmptyStr
    non_null_count: int = Field(ge=0)
    null_count: int = Field(ge=0)
    unique_count: int = Field(ge=0)
    examples: tuple[str, ...] = ()


class IdentifierValidation(FrozenPolarisBaseModel):
    """Validation summary for country or year identifiers."""

    column: NonEmptyStr | None = None
    present: bool
    non_null_count: int = Field(ge=0)
    invalid_count: int = Field(ge=0)
    examples: tuple[str, ...] = ()


class DatasetSchemaInspection(FrozenPolarisBaseModel):
    """Schema, variable, identifier, and missing-value profile for a real CSV."""

    path: Path
    row_count_inspected: int = Field(ge=0)
    total_row_count: int | None = Field(default=None, ge=0)
    columns: tuple[str, ...]
    column_count: int = Field(ge=0)
    variable_columns: tuple[str, ...] = ()
    country_identifier: IdentifierValidation
    year_identifier: IdentifierValidation
    missing_value_counts: tuple[tuple[str, int], ...] = ()
    column_profiles: tuple[ColumnProfile, ...] = ()


class ManifestValidationResult(FrozenPolarisBaseModel):
    """Result of comparing a manifest to a downloaded or prepared dataset."""

    dataset_id: NonEmptyStr
    source_path: Path
    manifest_path: Path | None = None
    checksum_matches: bool
    access_url_matches: bool
    missing_manifest_columns: tuple[str, ...] = ()
    unexpected_source_columns: tuple[str, ...] = ()
    compatible_with_phase3: bool


class VariableSummary(FrozenPolarisBaseModel):
    """Human-readable summary of one automatically discovered variable."""

    variable_id: NonEmptyStr
    source_field_name: NonEmptyStr
    role: NonEmptyStr
    data_type: NonEmptyStr
    non_null_count: int = Field(ge=0)
    null_count: int = Field(ge=0)
    unique_count: int = Field(ge=0)
    minimum: float | str | None = None
    maximum: float | str | None = None


class PipelineValidationResult(FrozenPolarisBaseModel):
    """End-to-end Phase 3 through Phase 9 validation status."""

    ingestion_succeeded: bool
    analysis_succeeded: bool
    evidence_extraction_succeeded: bool
    domain_assessments_succeeded: bool
    coordination_succeeded: bool
    synthesis_succeeded: bool
    report_generation_succeeded: bool
    analysis_result_id: NonEmptyStr
    evidence_artifact_id: NonEmptyStr
    coordinated_assessment_id: NonEmptyStr
    synthesis_artifact_id: NonEmptyStr
    report_id: NonEmptyStr
    accepted_row_count: int = Field(ge=0)
    analysis_sample_size: int = Field(ge=0)


class RealDatasetValidationResult(FrozenPolarisBaseModel):
    """Complete Phase 11 validation artifact."""

    discovered_datasets: tuple[DiscoveredDataset, ...]
    selected_dataset: DiscoveredDataset
    raw_schema_inspection: DatasetSchemaInspection
    prepared_schema_inspection: DatasetSchemaInspection
    manifest_validation: ManifestValidationResult
    variable_summaries: tuple[VariableSummary, ...]
    pipeline: PipelineValidationResult
    report: GeneratedReport
