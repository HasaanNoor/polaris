from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from polaris.ingestion import (
    IngestionConfiguration,
    IngestionRequest,
    UnexpectedColumnMode,
    ingest_dataset,
)
from polaris.providers import (
    ChecksumValidationError,
    DownloadRequest,
    EmptyDownloadError,
    ProviderDatasetNotFoundError,
    UnsupportedFormatError,
    default_provider_registry,
    download_dataset,
)
from polaris.providers.registry import DataProviderRegistry
from polaris.registry import DatasetCollectionType, DatasetRegistry, load_manifest

DATA_EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "data" / "examples"
FIXED_TIMESTAMP = datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)


def test_default_provider_registry_lists_supported_providers() -> None:
    registry = default_provider_registry()

    assert [provider.provider_id for provider in registry.list_providers()] == [
        "world_bank",
        "who",
        "unesco",
    ]


def test_who_datasets_are_listed_without_network() -> None:
    registry = default_provider_registry()

    datasets = registry.list_datasets("who")

    assert [dataset.dataset_id for dataset in datasets] == ["GHO"]
    assert datasets[0].title == "Global Health Observatory"


def test_download_generates_snapshot_metadata_and_manifest(tmp_path: Path) -> None:
    source = DATA_EXAMPLES_DIR / "world_bank_wdi_sample.csv"

    result = download_dataset(
        provider="world_bank",
        dataset="WDI",
        source_url=source.as_uri(),
        raw_root=tmp_path / "raw",
        manifest_root=tmp_path / "manifests",
        download_timestamp=FIXED_TIMESTAMP,
    )

    assert result.from_cache is False
    assert result.snapshot.path.exists()
    assert result.snapshot.metadata.checksum_sha256 == result.manifest.checksum
    assert result.manifest.retrieval_timestamp == FIXED_TIMESTAMP
    assert result.manifest.access_url == str(result.snapshot.path)
    assert result.manifest_path.exists()
    assert result.snapshot.metadata_path.exists()


def test_duplicate_checksum_returns_existing_snapshot(tmp_path: Path) -> None:
    source = DATA_EXAMPLES_DIR / "who_gho_sample.csv"

    first = download_dataset(
        provider="who",
        dataset="GHO",
        source_url=source.as_uri(),
        raw_root=tmp_path / "raw",
        manifest_root=tmp_path / "manifests",
        download_timestamp=FIXED_TIMESTAMP,
    )
    second = download_dataset(
        provider="who",
        dataset="GHO",
        source_url=source.as_uri(),
        raw_root=tmp_path / "raw",
        manifest_root=tmp_path / "manifests",
        download_timestamp=datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC),
    )

    assert second.from_cache is True
    assert second.snapshot.path == first.snapshot.path
    assert len(tuple((tmp_path / "raw" / "who").glob("*.csv"))) == 1


def test_checksum_validation_rejects_unexpected_content(tmp_path: Path) -> None:
    source = DATA_EXAMPLES_DIR / "unesco_uis_sample.csv"

    with pytest.raises(ChecksumValidationError):
        download_dataset(
            provider="unesco",
            dataset="UIS",
            source_url=source.as_uri(),
            raw_root=tmp_path / "raw",
            manifest_root=tmp_path / "manifests",
            expected_checksum="0" * 64,
            download_timestamp=FIXED_TIMESTAMP,
        )


def test_empty_download_rejected(tmp_path: Path) -> None:
    source = tmp_path / "empty.csv"
    source.write_text("", encoding="utf-8")

    with pytest.raises(EmptyDownloadError):
        download_dataset(
            provider="world_bank",
            dataset="WDI",
            source_url=source.as_uri(),
            raw_root=tmp_path / "raw",
            manifest_root=tmp_path / "manifests",
            download_timestamp=FIXED_TIMESTAMP,
        )


def test_unsupported_file_type_rejected(tmp_path: Path) -> None:
    source = tmp_path / "data.txt"
    source.write_text("x\n1\n", encoding="utf-8")

    with pytest.raises(UnsupportedFormatError):
        download_dataset(
            provider="world_bank",
            dataset="WDI",
            source_url=source.as_uri(),
            filename="data.txt",
            raw_root=tmp_path / "raw",
            manifest_root=tmp_path / "manifests",
            download_timestamp=FIXED_TIMESTAMP,
        )


def test_unknown_provider_dataset_rejected(tmp_path: Path) -> None:
    registry = default_provider_registry()

    with pytest.raises(ProviderDatasetNotFoundError):
        registry.get("world_bank").download_dataset(
            DownloadRequest(
                provider="world_bank",
                dataset="missing",
                raw_root=tmp_path / "raw",
                manifest_root=tmp_path / "manifests",
            )
        )


def test_download_request_checksum_shape_is_typed(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        DownloadRequest(
            provider="world_bank",
            dataset="WDI",
            raw_root=tmp_path / "raw",
            manifest_root=tmp_path / "manifests",
            expected_checksum="bad",
        )


def test_downloaded_manifest_integrates_with_dataset_registry(tmp_path: Path) -> None:
    result = download_dataset(
        provider="world_bank",
        dataset="WDI",
        source_url=(DATA_EXAMPLES_DIR / "world_bank_wdi_sample.csv").as_uri(),
        raw_root=tmp_path / "raw",
        manifest_root=tmp_path / "manifests",
        download_timestamp=FIXED_TIMESTAMP,
    )

    registry = DatasetRegistry([result.manifest])

    assert registry.contains(result.manifest.dataset_id)
    assert (
        registry.collection_type(result.manifest.dataset_id) is DatasetCollectionType.REAL_PROVIDER
    )
    assert registry.list_by_collection_type(DatasetCollectionType.REAL_PROVIDER) == (
        result.manifest,
    )
    assert registry.search()[0].collection_type is DatasetCollectionType.REAL_PROVIDER


def test_manifest_can_be_loaded_offline(tmp_path: Path) -> None:
    result = download_dataset(
        provider="unesco",
        dataset="UIS",
        source_url=(DATA_EXAMPLES_DIR / "unesco_uis_sample.csv").as_uri(),
        raw_root=tmp_path / "raw",
        manifest_root=tmp_path / "manifests",
        download_timestamp=FIXED_TIMESTAMP,
    )

    loaded = load_manifest(result.manifest_path)

    assert loaded == result.manifest
    assert loaded.access_url == str(result.snapshot.path)


def test_downloaded_snapshot_passes_phase3_ingestion(tmp_path: Path) -> None:
    result = download_dataset(
        provider="world_bank",
        dataset="WDI",
        source_url=(DATA_EXAMPLES_DIR / "world_bank_wdi_sample.csv").as_uri(),
        raw_root=tmp_path / "raw",
        manifest_root=tmp_path / "manifests",
        download_timestamp=FIXED_TIMESTAMP,
    )
    registry = DatasetRegistry([result.manifest])

    ingestion = ingest_dataset(
        registry=registry,
        request=IngestionRequest(
            dataset_id=result.manifest.dataset_id,
            source_path=result.snapshot.path,
            expected_checksum=result.snapshot.metadata.checksum_sha256,
        ),
    )

    assert ingestion.validation_report.analysis_ready is True
    assert ingestion.validation_report.accepted_row_count == 3


def test_provider_abstraction_can_be_supplied_explicitly(tmp_path: Path) -> None:
    provider_registry = DataProviderRegistry((default_provider_registry().get("who"),))

    result = download_dataset(
        provider="who",
        dataset="GHO",
        registry=provider_registry,
        source_url=(DATA_EXAMPLES_DIR / "who_gho_sample.csv").as_uri(),
        raw_root=tmp_path / "raw",
        manifest_root=tmp_path / "manifests",
        download_timestamp=FIXED_TIMESTAMP,
    )

    assert result.provider_metadata.provider_id == "who"


def test_phase3_can_load_provider_snapshot_with_permissive_config(tmp_path: Path) -> None:
    result = download_dataset(
        provider="who",
        dataset="GHO",
        source_url=(DATA_EXAMPLES_DIR / "who_gho_sample.csv").as_uri(),
        raw_root=tmp_path / "raw",
        manifest_root=tmp_path / "manifests",
        download_timestamp=FIXED_TIMESTAMP,
    )
    registry = DatasetRegistry([result.manifest])

    ingestion = ingest_dataset(
        registry=registry,
        request=IngestionRequest(
            dataset_id=result.manifest.dataset_id,
            source_path=result.snapshot.path,
            expected_checksum=result.manifest.checksum,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE
            ),
        ),
    )

    assert ingestion.dataset_manifest == result.manifest
