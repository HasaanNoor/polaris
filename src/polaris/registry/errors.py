"""Domain exceptions for dataset registry and manifest loading."""

from pathlib import Path


class DatasetRegistryError(Exception):
    """Base error for dataset registry operations."""


class DuplicateDatasetError(DatasetRegistryError):
    """Raised when a registry would contain duplicate dataset identifiers."""

    def __init__(self, dataset_id: str) -> None:
        super().__init__(f'dataset identifier "{dataset_id}" is already registered')
        self.dataset_id = dataset_id


class DatasetNotFoundError(DatasetRegistryError):
    """Raised when a requested dataset identifier is absent."""

    def __init__(self, dataset_id: str) -> None:
        super().__init__(f'dataset identifier "{dataset_id}" is not registered')
        self.dataset_id = dataset_id


class ManifestLoadError(DatasetRegistryError):
    """Raised when a manifest path cannot be read or parsed as JSON."""

    def __init__(self, path: Path, message: str) -> None:
        super().__init__(f"{path}: {message}")
        self.path = path


class ManifestValidationError(DatasetRegistryError):
    """Raised when JSON content fails DatasetManifest schema validation."""

    def __init__(self, path: Path, message: str) -> None:
        super().__init__(f"{path}: {message}")
        self.path = path
