"""Deterministic provider acquisition errors."""

from pathlib import Path


class ProviderError(Exception):
    """Base class for provider acquisition failures."""


class ProviderNotFoundError(ProviderError):
    def __init__(self, provider: str) -> None:
        super().__init__(f'provider "{provider}" is not registered')
        self.provider = provider


class ProviderDatasetNotFoundError(ProviderError):
    def __init__(self, provider: str, dataset: str) -> None:
        super().__init__(f'provider "{provider}" does not expose dataset "{dataset}"')
        self.provider = provider
        self.dataset = dataset


class DownloadError(ProviderError):
    """Raised when source acquisition fails."""


class EmptyDownloadError(DownloadError):
    def __init__(self, source_url: str) -> None:
        super().__init__(f"{source_url}: downloaded file is empty")
        self.source_url = source_url


class UnsupportedFormatError(DownloadError):
    def __init__(self, path: str | Path, supported: tuple[str, ...]) -> None:
        super().__init__(f"{path}: unsupported file type; expected one of {', '.join(supported)}")
        self.path = Path(path)
        self.supported = supported


class ChecksumValidationError(DownloadError):
    def __init__(self, path: str | Path, expected: str, observed: str) -> None:
        super().__init__(
            f"{path}: checksum mismatch; expected {expected.lower()}, observed {observed}"
        )
        self.path = Path(path)
        self.expected = expected.lower()
        self.observed = observed


class DuplicateSnapshotError(DownloadError):
    def __init__(self, checksum: str, existing_path: str | Path) -> None:
        super().__init__(f"snapshot with checksum {checksum} already exists at {existing_path}")
        self.checksum = checksum
        self.existing_path = Path(existing_path)


class ManifestCompatibilityError(ProviderError):
    """Raised when provider metadata cannot produce a DatasetManifest."""


class ProviderMetadataError(ProviderError):
    """Raised when provider or dataset metadata is incomplete."""
