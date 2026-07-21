"""Small orchestration entry point for local dataset ingestion."""

from datetime import UTC, datetime

from polaris import __version__
from polaris.ingestion.errors import (
    ChecksumMismatchError,
    DatasetValidationError,
    ManifestColumnMismatchError,
)
from polaris.ingestion.loader import calculate_sha256, file_size, load_tabular_file
from polaris.ingestion.models import (
    ColumnMapping,
    DataQualityProfile,
    DatasetIngestionResult,
    IngestionProvenance,
    IngestionRequest,
    SourceFileMetadata,
    StructuralValidationReport,
    ValidationFinding,
    ValidationFindingCode,
    ValidationSeverity,
)
from polaris.ingestion.normalization import normalize_rows
from polaris.ingestion.profiling import build_quality_profile
from polaris.ingestion.validation import map_manifest_columns
from polaris.registry import DatasetRegistry


def ingest_dataset(
    *,
    registry: DatasetRegistry,
    request: IngestionRequest,
) -> DatasetIngestionResult:
    """Resolve a manifest and ingest a local CSV source file deterministically."""

    manifest = registry.get(request.dataset_id)
    checksum = calculate_sha256(request.source_path)
    if request.expected_checksum is not None and checksum != request.expected_checksum.lower():
        raise ChecksumMismatchError(request.source_path, request.expected_checksum, checksum)

    loaded_file = load_tabular_file(request.source_path, request.configuration)
    mappings, missing_columns, unexpected_columns, structural_findings = map_manifest_columns(
        manifest,
        loaded_file,
        request.configuration,
    )

    normalized_records, normalization_findings = normalize_rows(
        manifest,
        loaded_file,
        mappings,
        request.configuration,
    )
    source_row_count = len(loaded_file.rows) + len(loaded_file.malformed_rows)
    rejected_row_count = source_row_count - len(normalized_records)
    all_findings = structural_findings + normalization_findings
    retained_findings = _retain_findings(
        all_findings,
        request.configuration.max_validation_error_samples,
    )
    report = _build_report(
        request=request,
        source_row_count=source_row_count,
        accepted_row_count=len(normalized_records),
        rejected_row_count=rejected_row_count,
        source_columns=loaded_file.source_columns,
        mapped_columns=mappings,
        missing_columns=missing_columns,
        unexpected_columns=unexpected_columns,
        findings=retained_findings,
    )

    _raise_for_unusable_structure(report)

    quality_profile = build_quality_profile(
        manifest,
        mappings,
        normalized_records,
        all_findings,
        source_row_count=source_row_count,
        rejected_row_count=rejected_row_count,
    )
    timestamp = datetime.now(UTC)
    source_metadata = SourceFileMetadata(
        source_path=str(request.source_path),
        checksum_sha256=checksum,
        file_size_bytes=file_size(request.source_path),
    )
    provenance = IngestionProvenance(
        dataset_id=request.dataset_id,
        source_path=str(request.source_path),
        checksum_sha256=checksum,
        file_size_bytes=source_metadata.file_size_bytes,
        ingestion_timestamp=timestamp,
        configuration=request.configuration,
        software_version=f"polaris-{__version__}",
    )

    return DatasetIngestionResult(
        dataset_manifest=manifest,
        ingestion_request=request,
        source_metadata=source_metadata,
        checksum_sha256=checksum,
        normalized_records=normalized_records,
        validation_report=report,
        quality_profile=quality_profile,
        provenance=provenance,
        provenance_record=None,
        ingestion_timestamp=timestamp,
    )


def _build_report(
    *,
    request: IngestionRequest,
    source_row_count: int,
    accepted_row_count: int,
    rejected_row_count: int,
    source_columns: tuple[str, ...],
    mapped_columns: tuple[ColumnMapping, ...],
    missing_columns: tuple[str, ...],
    unexpected_columns: tuple[str, ...],
    findings: tuple[ValidationFinding, ...],
) -> StructuralValidationReport:
    has_fatal = any(finding.severity is ValidationSeverity.FATAL for finding in findings)
    has_error = any(finding.severity is ValidationSeverity.ERROR for finding in findings)
    validation_succeeded = not has_fatal and not has_error
    analysis_ready = validation_succeeded and accepted_row_count > 0
    return StructuralValidationReport(
        source_path=str(request.source_path),
        dataset_id=request.dataset_id,
        source_row_count=source_row_count,
        accepted_row_count=accepted_row_count,
        rejected_row_count=rejected_row_count,
        source_columns=source_columns,
        mapped_columns=mapped_columns,
        missing_columns=missing_columns,
        unexpected_columns=unexpected_columns,
        validation_findings=findings,
        parsing_succeeded=True,
        validation_succeeded=validation_succeeded,
        analysis_ready=analysis_ready,
    )


def _retain_findings(
    findings: tuple[ValidationFinding, ...],
    max_samples: int,
) -> tuple[ValidationFinding, ...]:
    structural_codes = {
        ValidationFindingCode.EMPTY_DATASET,
        ValidationFindingCode.MISSING_REQUIRED_COLUMN,
        ValidationFindingCode.UNEXPECTED_COLUMN,
        ValidationFindingCode.DUPLICATE_COLUMN,
        ValidationFindingCode.MALFORMED_ROW,
        ValidationFindingCode.UNMAPPED_VARIABLE,
        ValidationFindingCode.AMBIGUOUS_COLUMN_MAPPING,
        ValidationFindingCode.INVALID_MANIFEST_DECLARATION,
    }
    required_findings = tuple(
        finding
        for finding in findings
        if finding.severity is ValidationSeverity.FATAL or finding.code in structural_codes
    )
    required_ids = {id(finding) for finding in required_findings}
    sample_candidates = tuple(finding for finding in findings if id(finding) not in required_ids)
    if max_samples == 0:
        return required_findings
    return required_findings + sample_candidates[:max_samples]


def _raise_for_unusable_structure(report: StructuralValidationReport) -> None:
    fatal_or_structural_codes = {
        "empty_dataset",
        "missing_required_column",
        "unexpected_column",
        "duplicate_column",
        "malformed_row",
        "ambiguous_column_mapping",
        "invalid_manifest_declaration",
    }
    structural_errors = tuple(
        finding
        for finding in report.validation_findings
        if finding.severity in {ValidationSeverity.FATAL, ValidationSeverity.ERROR}
        and finding.code.value in fatal_or_structural_codes
    )
    if report.missing_columns:
        raise ManifestColumnMismatchError(
            f"{report.source_path}: required manifest columns are missing: "
            + ", ".join(report.missing_columns),
            source_path=report.source_path,
            dataset_id=report.dataset_id,
        )
    if structural_errors:
        first = structural_errors[0]
        raise DatasetValidationError(
            first.message,
            report=report,
            source_path=report.source_path,
            dataset_id=report.dataset_id,
            row_number=first.row_number,
            column_name=first.source_column,
        )
    if report.source_row_count > 0 and report.accepted_row_count == 0:
        raise DatasetValidationError(
            f"{report.source_path}: no source rows were accepted after validation",
            report=report,
            source_path=report.source_path,
            dataset_id=report.dataset_id,
        )


def empty_quality_profile(dataset_id: str) -> DataQualityProfile:
    """Return an empty profile for callers that need a typed placeholder."""

    return DataQualityProfile(dataset_id=dataset_id, row_count=0, accepted_row_count=0)
