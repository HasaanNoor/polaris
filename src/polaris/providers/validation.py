"""Provider snapshot and manifest validation helpers."""

from pathlib import Path

from pydantic import ValidationError

from polaris.ingestion.loader import calculate_sha256, file_size
from polaris.providers.base import DatasetSnapshot, ProviderDataset, ProviderMetadata
from polaris.providers.errors import (
    ChecksumValidationError,
    EmptyDownloadError,
    ManifestCompatibilityError,
    ProviderMetadataError,
    UnsupportedFormatError,
)
from polaris.schemas.dataset import DatasetManifest

PHASE3_SUPPORTED_FORMATS = (".csv",)


def validate_provider_metadata(metadata: ProviderMetadata) -> None:
    missing = [
        field
        for field in ("provider_id", "name", "homepage_url", "description")
        if not getattr(metadata, field)
    ]
    if missing:
        raise ProviderMetadataError(f"provider metadata missing fields: {', '.join(missing)}")


def validate_provider_dataset(dataset: ProviderDataset) -> None:
    if not dataset.variables:
        raise ProviderMetadataError(f"{dataset.dataset_id}: provider dataset has no variables")
    if dataset.format not in PHASE3_SUPPORTED_FORMATS:
        raise UnsupportedFormatError(dataset.source_url, PHASE3_SUPPORTED_FORMATS)


def validate_snapshot(snapshot: DatasetSnapshot, supported_formats: tuple[str, ...]) -> None:
    path = Path(snapshot.metadata.snapshot_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() not in supported_formats:
        raise UnsupportedFormatError(path, supported_formats)
    if file_size(path) == 0:
        raise EmptyDownloadError(snapshot.metadata.source_url)

    observed = calculate_sha256(path)
    expected = snapshot.metadata.checksum_sha256
    if observed != expected:
        raise ChecksumValidationError(path, expected, observed)


def validate_manifest_compatibility(manifest: DatasetManifest) -> None:
    try:
        DatasetManifest.model_validate(manifest.model_dump(mode="json"))
    except ValidationError as exc:
        raise ManifestCompatibilityError(str(exc)) from exc
