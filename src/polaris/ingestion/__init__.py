"""Local tabular dataset ingestion for Polaris."""

from polaris.ingestion.errors import (
    ChecksumMismatchError,
    DatasetIngestionError,
    DatasetValidationError,
    DuplicateColumnError,
    MalformedTabularDataError,
    ManifestColumnMismatchError,
    SourceFileNotFoundError,
    SourceFileReadError,
)
from polaris.ingestion.loader import calculate_sha256, load_tabular_file
from polaris.ingestion.models import (
    DataQualityProfile,
    DatasetIngestionResult,
    IngestionConfiguration,
    IngestionProvenance,
    IngestionRequest,
    NormalizedRecord,
    SourceFileMetadata,
    StructuralValidationReport,
    UnexpectedColumnMode,
    ValidationFinding,
    ValidationFindingCode,
    ValidationSeverity,
    VariableQualityProfile,
)
from polaris.ingestion.service import ingest_dataset

__all__ = [
    "ChecksumMismatchError",
    "DataQualityProfile",
    "DatasetIngestionError",
    "DatasetIngestionResult",
    "DatasetValidationError",
    "DuplicateColumnError",
    "IngestionConfiguration",
    "IngestionProvenance",
    "IngestionRequest",
    "MalformedTabularDataError",
    "ManifestColumnMismatchError",
    "NormalizedRecord",
    "SourceFileMetadata",
    "SourceFileNotFoundError",
    "SourceFileReadError",
    "StructuralValidationReport",
    "UnexpectedColumnMode",
    "ValidationFinding",
    "ValidationFindingCode",
    "ValidationSeverity",
    "VariableQualityProfile",
    "calculate_sha256",
    "ingest_dataset",
    "load_tabular_file",
]
