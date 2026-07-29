"""Shared implementation for static provider metadata adapters."""

from pathlib import Path

from polaris.providers.base import (
    DatasetSnapshot,
    DownloadRequest,
    DownloadResult,
    Provider,
    ProviderDataset,
    ProviderManifest,
    ProviderMetadata,
)
from polaris.providers.downloader import acquire_snapshot
from polaris.providers.errors import ProviderDatasetNotFoundError
from polaris.providers.manifest import create_dataset_manifest
from polaris.providers.validation import (
    validate_provider_dataset,
    validate_provider_metadata,
    validate_snapshot,
)


class StaticFileProvider(Provider):
    """Provider adapter backed by declared downloadable file metadata."""

    def __init__(
        self,
        *,
        metadata: ProviderMetadata,
        datasets: tuple[ProviderDataset, ...],
    ) -> None:
        validate_provider_metadata(metadata)
        for dataset in datasets:
            validate_provider_dataset(dataset)
        self._metadata = metadata
        self._datasets = datasets
        self.provider_id = metadata.provider_id

    def metadata(self) -> ProviderMetadata:
        return self._metadata

    def available_datasets(self) -> tuple[ProviderDataset, ...]:
        return self._datasets

    def download_dataset(self, request: DownloadRequest) -> DownloadResult:
        dataset = self.get_dataset(request.dataset)
        if dataset is None:
            raise ProviderDatasetNotFoundError(self.provider_id, request.dataset)

        metadata, from_cache = acquire_snapshot(
            request=request,
            dataset=dataset,
            provider_id=self.provider_id,
        )
        snapshot = DatasetSnapshot(
            metadata=metadata,
            metadata_path=Path(f"{metadata.snapshot_path}.metadata.json"),
        )
        self.validate_download(snapshot)
        provider_manifest = self.create_manifest(
            dataset=dataset,
            snapshot=snapshot,
            manifest_root=request.manifest_root,
        )
        return DownloadResult(
            request=request,
            provider_metadata=self.metadata(),
            provider_dataset=dataset,
            snapshot=snapshot,
            manifest=provider_manifest.dataset_manifest,
            manifest_path=provider_manifest.manifest_path,
            from_cache=from_cache,
        )

    def validate_download(self, snapshot: DatasetSnapshot) -> None:
        validate_snapshot(snapshot, tuple(self.metadata().supported_formats))

    def create_manifest(
        self,
        *,
        dataset: ProviderDataset,
        snapshot: DatasetSnapshot,
        manifest_root: Path,
    ) -> ProviderManifest:
        return create_dataset_manifest(
            provider=self.metadata(),
            dataset=dataset,
            snapshot=snapshot,
            manifest_root=manifest_root,
        )
