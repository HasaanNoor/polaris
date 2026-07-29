"""Provider interfaces and typed acquisition contracts."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path

from pydantic import Field, field_validator

from polaris.ingestion.models import SHA256_PATTERN
from polaris.schemas.common import (
    AwareDatetime,
    DataType,
    FrozenPolarisBaseModel,
    GeographicScope,
    NonEmptyStr,
    PolarisBaseModel,
    SchemaVersion,
    TemporalScope,
    VariableRole,
)
from polaris.schemas.dataset import DatasetManifest, DatasetVariable


class SnapshotMetadata(FrozenPolarisBaseModel):
    """Content identity and source metadata for an immutable raw snapshot."""

    provider: NonEmptyStr
    dataset_id: NonEmptyStr
    source_url: NonEmptyStr
    original_filename: NonEmptyStr
    snapshot_path: Path
    checksum_sha256: str = Field(pattern=SHA256_PATTERN)
    file_size_bytes: int = Field(ge=1)
    downloaded_at: AwareDatetime
    format: NonEmptyStr
    schema_version: SchemaVersion = "1.0.0"


class DatasetSnapshot(FrozenPolarisBaseModel):
    """A local immutable raw provider dataset and its metadata file."""

    metadata: SnapshotMetadata
    metadata_path: Path

    @property
    def path(self) -> Path:
        return self.metadata.snapshot_path


class ProviderMetadata(FrozenPolarisBaseModel):
    """Static metadata for a public data provider."""

    provider_id: NonEmptyStr
    name: NonEmptyStr
    homepage_url: NonEmptyStr
    description: NonEmptyStr
    license: NonEmptyStr | None = None
    citation: NonEmptyStr | None = None
    supported_formats: tuple[NonEmptyStr, ...] = (".csv",)
    schema_version: SchemaVersion = "1.0.0"


class ProviderDataset(FrozenPolarisBaseModel):
    """Provider dataset metadata sufficient to acquire and manifest a snapshot."""

    dataset_id: NonEmptyStr
    title: NonEmptyStr
    source_url: NonEmptyStr
    description: NonEmptyStr
    license: NonEmptyStr | None = None
    citation: NonEmptyStr | None = None
    publication_date: NonEmptyStr | None = None
    version: NonEmptyStr | None = None
    geographic_coverage: GeographicScope
    temporal_coverage: TemporalScope
    variables: tuple[DatasetVariable, ...] = Field(min_length=1)
    units: tuple[NonEmptyStr, ...] = ()
    frequency: NonEmptyStr | None = None
    format: NonEmptyStr = ".csv"
    methodology_reference: NonEmptyStr | None = None

    @field_validator("format")
    @classmethod
    def normalize_format(cls, value: str) -> str:
        normalized = value.lower().strip()
        if not normalized.startswith("."):
            normalized = f".{normalized}"
        return normalized


class DownloadRequest(FrozenPolarisBaseModel):
    """Request to acquire one provider dataset as an immutable snapshot."""

    provider: NonEmptyStr
    dataset: NonEmptyStr
    raw_root: Path = Path("data/raw")
    manifest_root: Path = Path("data/manifests")
    source_url: NonEmptyStr | None = None
    filename: NonEmptyStr | None = None
    expected_checksum: str | None = Field(default=None, pattern=SHA256_PATTERN)
    download_timestamp: AwareDatetime | None = None


class ProviderManifest(FrozenPolarisBaseModel):
    """Provider-side manifest bundle returned after acquisition."""

    dataset_manifest: DatasetManifest
    snapshot_metadata: SnapshotMetadata
    manifest_path: Path


class DownloadResult(FrozenPolarisBaseModel):
    """Complete result of a provider acquisition."""

    request: DownloadRequest
    provider_metadata: ProviderMetadata
    provider_dataset: ProviderDataset
    snapshot: DatasetSnapshot
    manifest: DatasetManifest
    manifest_path: Path
    from_cache: bool = False
    schema_version: SchemaVersion = "1.0.0"


class ProviderRegistry(PolarisBaseModel):
    """Serializable view of registered providers."""

    providers: tuple[ProviderMetadata, ...] = ()


class Provider(ABC):
    """Interface implemented by deterministic provider adapters."""

    provider_id: str

    @abstractmethod
    def metadata(self) -> ProviderMetadata:
        """Return provider-level metadata without network access."""

    @abstractmethod
    def available_datasets(self) -> tuple[ProviderDataset, ...]:
        """Return statically declared downloadable datasets."""

    def get_dataset(self, dataset_id: str) -> ProviderDataset | None:
        normalized = dataset_id.lower()
        for dataset in self.available_datasets():
            if dataset.dataset_id.lower() == normalized:
                return dataset
        return None

    @abstractmethod
    def download_dataset(self, request: DownloadRequest) -> DownloadResult:
        """Acquire a dataset and return its local snapshot and manifest."""

    @abstractmethod
    def validate_download(self, snapshot: DatasetSnapshot) -> None:
        """Validate checksum, type, and file integrity for a snapshot."""

    @abstractmethod
    def create_manifest(
        self,
        *,
        dataset: ProviderDataset,
        snapshot: DatasetSnapshot,
        manifest_root: Path,
    ) -> ProviderManifest:
        """Create a Phase 3-compatible DatasetManifest for a snapshot."""


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def provider_variable(
    variable_id: str,
    label: str,
    data_type: DataType,
    role: VariableRole,
    *,
    source_field_name: str | None = None,
    description: str | None = None,
    unit: str | None = None,
    missing: tuple[str, ...] = ("null", "NA", "N/A"),
) -> DatasetVariable:
    """Build a DatasetVariable for provider metadata declarations."""

    return DatasetVariable(
        variable_id=variable_id,
        label=label,
        description=description,
        unit=unit,
        data_type=data_type,
        role=role,
        source_field_name=source_field_name or variable_id,
        missing_value_representation=list(missing),
    )
