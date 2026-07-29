"""Manifest generation for acquired provider snapshots."""

from pathlib import Path

from polaris.providers.base import (
    DatasetSnapshot,
    ProviderDataset,
    ProviderManifest,
    ProviderMetadata,
)
from polaris.providers.validation import validate_manifest_compatibility
from polaris.schemas.common import DatasetStatus
from polaris.schemas.dataset import DatasetManifest, RevisionMetadata


def create_dataset_manifest(
    *,
    provider: ProviderMetadata,
    dataset: ProviderDataset,
    snapshot: DatasetSnapshot,
    manifest_root: str | Path,
) -> ProviderManifest:
    """Build and persist a Phase 3-compatible DatasetManifest."""

    metadata = snapshot.metadata
    manifest = DatasetManifest(
        dataset_id=f"{provider.provider_id}_{dataset.dataset_id.lower()}_{metadata.checksum_sha256[:12]}",
        title=dataset.title,
        provider=provider.name,
        source_url=metadata.source_url,
        access_url=str(metadata.snapshot_path),
        description=_description_with_citation(dataset),
        license=dataset.license or provider.license,
        status=DatasetStatus.REVIEWED_CANDIDATE,
        geographic_coverage=dataset.geographic_coverage,
        temporal_coverage=dataset.temporal_coverage,
        revision_metadata=RevisionMetadata(
            release_date=dataset.publication_date,
            update_frequency=dataset.frequency,
            source_version=dataset.version,
        ),
        variables=list(dataset.variables),
        units=list(dataset.units),
        frequency=dataset.frequency,
        methodology_reference=dataset.methodology_reference,
        source_version=dataset.version,
        retrieval_timestamp=metadata.downloaded_at,
        checksum=metadata.checksum_sha256,
    )
    validate_manifest_compatibility(manifest)

    destination = Path(manifest_root) / f"{manifest.dataset_id}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return ProviderManifest(
        dataset_manifest=manifest,
        snapshot_metadata=metadata,
        manifest_path=destination,
    )


def _description_with_citation(dataset: ProviderDataset) -> str:
    if dataset.citation is None:
        return dataset.description
    return f"{dataset.description} Citation: {dataset.citation}"
