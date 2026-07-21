"""Domain exceptions for local dataset ingestion."""

from pathlib import Path


class DatasetIngestionError(Exception):
    """Base error for local ingestion operations."""

    def __init__(
        self,
        message: str,
        *,
        source_path: str | Path | None = None,
        dataset_id: str | None = None,
        row_number: int | None = None,
        column_name: str | None = None,
    ) -> None:
        super().__init__(message)
        self.source_path = Path(source_path) if source_path is not None else None
        self.dataset_id = dataset_id
        self.row_number = row_number
        self.column_name = column_name


class SourceFileNotFoundError(DatasetIngestionError):
    """Raised when the requested local source path does not exist."""


class SourceFileReadError(DatasetIngestionError):
    """Raised when a local source file cannot be read."""


class MalformedTabularDataError(DatasetIngestionError):
    """Raised when CSV parsing cannot continue deterministically."""


class DuplicateColumnError(DatasetIngestionError):
    """Raised when a source header contains duplicate column names."""


class ManifestColumnMismatchError(DatasetIngestionError):
    """Raised when manifest declarations cannot be mapped to source columns."""


class ChecksumMismatchError(DatasetIngestionError):
    """Raised when the source checksum does not match the expected checksum."""

    def __init__(
        self,
        source_path: str | Path,
        expected_checksum: str,
        actual_checksum: str,
    ) -> None:
        super().__init__(
            f"{source_path}: expected SHA-256 {expected_checksum}, got {actual_checksum}",
            source_path=source_path,
        )
        self.expected_checksum = expected_checksum
        self.actual_checksum = actual_checksum


class DatasetValidationError(DatasetIngestionError):
    """Raised when parsed data is not analysis-ready under Phase 3 rules."""

    def __init__(
        self,
        message: str,
        *,
        report: object | None = None,
        source_path: str | Path | None = None,
        dataset_id: str | None = None,
        row_number: int | None = None,
        column_name: str | None = None,
    ) -> None:
        super().__init__(
            message,
            source_path=source_path,
            dataset_id=dataset_id,
            row_number=row_number,
            column_name=column_name,
        )
        self.report = report
