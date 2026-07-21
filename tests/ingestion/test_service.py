from datetime import UTC
from pathlib import Path

import pytest
from pydantic import ValidationError

from polaris.ingestion import (
    ChecksumMismatchError,
    DatasetValidationError,
    IngestionConfiguration,
    IngestionRequest,
    ManifestColumnMismatchError,
    UnexpectedColumnMode,
    ValidationFindingCode,
    calculate_sha256,
    ingest_dataset,
)
from polaris.registry import DatasetNotFoundError, DatasetRegistry
from polaris.schemas.common import DataType
from tests.ingestion.helpers import manifest_with_variables, variable, write_csv


def test_configuration_defaults_and_immutability() -> None:
    configuration = IngestionConfiguration()

    assert configuration.encoding == "utf-8"
    assert configuration.delimiter == ","
    assert configuration.header is True
    with pytest.raises(ValidationError):
        configuration.delimiter = "\t"  # type: ignore[misc]


def test_configuration_rejects_unknown_and_invalid_values() -> None:
    with pytest.raises(ValidationError):
        IngestionConfiguration.model_validate({"unknown": True})
    with pytest.raises(ValidationError):
        IngestionConfiguration(delimiter="||")
    with pytest.raises(ValidationError):
        IngestionConfiguration(header=False)


def test_request_checksum_validation(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        IngestionRequest(
            dataset_id="test",
            source_path=tmp_path / "data.csv",
            expected_checksum="bad",
        )
    with pytest.raises(ValidationError):
        IngestionRequest(
            dataset_id="test",
            source_path=tmp_path / "data.csv",
            configuration=IngestionConfiguration(require_source_checksum=True),
        )


def test_ingest_successful_analysis_ready_result(tmp_path: Path) -> None:
    manifest = manifest_with_variables([variable("amount", DataType.FLOAT)])
    registry = DatasetRegistry([manifest])
    path = write_csv(tmp_path / "data.csv", [["amount"], ["1.5"], ["2.0"]])

    result = ingest_dataset(
        registry=registry,
        request=IngestionRequest(dataset_id=manifest.dataset_id, source_path=path),
    )

    assert result.dataset_manifest == manifest
    assert result.validation_report.analysis_ready is True
    assert result.normalized_records[0].values == {"amount": 1.5}
    assert result.quality_profile.variables[0].maximum == 2.0
    assert result.provenance.dataset_id == manifest.dataset_id
    assert result.provenance.source_path == str(path)
    assert result.provenance.ingestion_timestamp.tzinfo == UTC
    assert result.provenance.configuration == IngestionConfiguration()


def test_checksum_mismatch(tmp_path: Path) -> None:
    manifest = manifest_with_variables([variable("amount", DataType.FLOAT)])
    registry = DatasetRegistry([manifest])
    path = write_csv(tmp_path / "data.csv", [["amount"], ["1.5"]])

    with pytest.raises(ChecksumMismatchError):
        ingest_dataset(
            registry=registry,
            request=IngestionRequest(
                dataset_id=manifest.dataset_id,
                source_path=path,
                expected_checksum="0" * 64,
            ),
        )


def test_checksum_and_file_size_recorded(tmp_path: Path) -> None:
    manifest = manifest_with_variables([variable("amount", DataType.FLOAT)])
    registry = DatasetRegistry([manifest])
    path = write_csv(tmp_path / "data.csv", [["amount"], ["1.5"]])
    checksum = calculate_sha256(path)

    result = ingest_dataset(
        registry=registry,
        request=IngestionRequest(
            dataset_id=manifest.dataset_id,
            source_path=path,
            expected_checksum=checksum,
        ),
    )

    assert result.checksum_sha256 == checksum
    assert result.source_metadata.file_size_bytes == path.stat().st_size


def test_missing_required_column_rejected(tmp_path: Path) -> None:
    manifest = manifest_with_variables([variable("amount", DataType.FLOAT)])
    registry = DatasetRegistry([manifest])
    path = write_csv(tmp_path / "data.csv", [["other"], ["1.5"]])

    with pytest.raises(ManifestColumnMismatchError):
        ingest_dataset(
            registry=registry,
            request=IngestionRequest(dataset_id=manifest.dataset_id, source_path=path),
        )


def test_unexpected_column_strict_rejected_and_permissive_retained(tmp_path: Path) -> None:
    manifest = manifest_with_variables([variable("amount", DataType.FLOAT)])
    registry = DatasetRegistry([manifest])
    path = write_csv(tmp_path / "data.csv", [["amount", "extra"], ["1.5", "x"]])

    with pytest.raises(DatasetValidationError):
        ingest_dataset(
            registry=registry,
            request=IngestionRequest(dataset_id=manifest.dataset_id, source_path=path),
        )

    result = ingest_dataset(
        registry=registry,
        request=IngestionRequest(
            dataset_id=manifest.dataset_id,
            source_path=path,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE
            ),
        ),
    )

    assert result.validation_report.unexpected_columns == ("extra",)
    assert (
        result.validation_report.validation_findings[0].code
        is ValidationFindingCode.UNEXPECTED_COLUMN
    )
    assert result.validation_report.analysis_ready is True


def test_invalid_values_create_typed_findings_and_rejected_rows(tmp_path: Path) -> None:
    manifest = manifest_with_variables([variable("amount", DataType.INTEGER)])
    registry = DatasetRegistry([manifest])
    path = write_csv(tmp_path / "data.csv", [["amount"], ["1"], ["bad"]])

    result = ingest_dataset(
        registry=registry,
        request=IngestionRequest(dataset_id=manifest.dataset_id, source_path=path),
    )

    assert result.validation_report.accepted_row_count == 1
    assert result.validation_report.rejected_row_count == 1
    assert result.validation_report.validation_succeeded is False
    assert result.validation_report.validation_findings[0].raw_value == "bad"


def test_max_retained_finding_samples(tmp_path: Path) -> None:
    manifest = manifest_with_variables([variable("amount", DataType.INTEGER)])
    registry = DatasetRegistry([manifest])
    path = write_csv(tmp_path / "data.csv", [["amount"], ["bad"], ["worse"], ["1"]])

    result = ingest_dataset(
        registry=registry,
        request=IngestionRequest(
            dataset_id=manifest.dataset_id,
            source_path=path,
            configuration=IngestionConfiguration(max_validation_error_samples=1),
        ),
    )

    invalid_findings = [
        finding
        for finding in result.validation_report.validation_findings
        if finding.code is ValidationFindingCode.INVALID_VALUE_TYPE
    ]
    assert len(invalid_findings) == 1


def test_unknown_dataset_identifier(tmp_path: Path) -> None:
    registry = DatasetRegistry()
    path = write_csv(tmp_path / "data.csv", [["amount"], ["1"]])

    with pytest.raises(DatasetNotFoundError):
        ingest_dataset(
            registry=registry,
            request=IngestionRequest(dataset_id="missing", source_path=path),
        )
