"""Official public dataset provider acquisition."""

from polaris.providers.base import (
    DatasetSnapshot,
    DownloadRequest,
    DownloadResult,
    Provider,
    ProviderDataset,
    ProviderManifest,
    ProviderMetadata,
    ProviderRegistry,
    SnapshotMetadata,
)
from polaris.providers.errors import (
    ChecksumValidationError,
    DownloadError,
    DuplicateSnapshotError,
    EmptyDownloadError,
    ManifestCompatibilityError,
    ProviderDatasetNotFoundError,
    ProviderError,
    ProviderMetadataError,
    ProviderNotFoundError,
    UnsupportedFormatError,
)
from polaris.providers.registry import (
    DataProviderRegistry,
    default_provider_registry,
    download_dataset,
)

__all__ = [
    "ChecksumValidationError",
    "DataProviderRegistry",
    "DatasetSnapshot",
    "DownloadError",
    "DownloadRequest",
    "DownloadResult",
    "DuplicateSnapshotError",
    "EmptyDownloadError",
    "ManifestCompatibilityError",
    "Provider",
    "ProviderDataset",
    "ProviderDatasetNotFoundError",
    "ProviderError",
    "ProviderManifest",
    "ProviderMetadata",
    "ProviderMetadataError",
    "ProviderNotFoundError",
    "ProviderRegistry",
    "SnapshotMetadata",
    "UnsupportedFormatError",
    "default_provider_registry",
    "download_dataset",
]
