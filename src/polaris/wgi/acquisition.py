"""Official World Bank WGI acquisition."""

from __future__ import annotations

from pathlib import Path

from polaris.providers.base import DownloadRequest, ProviderDataset, utc_now
from polaris.providers.downloader import acquire_snapshot
from polaris.schemas.common import DataType, GeographicScope, TemporalScope, VariableRole
from polaris.schemas.dataset import DatasetVariable
from polaris.wgi.mappings import wgi_mapping_registry
from polaris.wgi.models import (
    WGI_API_URL,
    WGI_SOURCE_ID,
    WGISnapshotReference,
)


def wgi_dimension_download_url(dimension_code: str) -> str:
    """Return the official World Bank API ZIP URL for one WGI dimension."""

    indicators = ";".join(
        [
            f"GOV_WGI_{dimension_code}.EST",
            f"GOV_WGI_{dimension_code}.SE",
            f"GOV_WGI_{dimension_code}.SR",
            f"GOV_WGI_{dimension_code}.SC",
            f"GOV_WGI_{dimension_code}.SC_LB",
            f"GOV_WGI_{dimension_code}.SC_UB",
        ]
    )
    return (
        f"{WGI_API_URL}/country/all/indicator/{indicators}"
        f"?source={WGI_SOURCE_ID}&downloadformat=csv&dataformat=list"
    )


def download_wgi_data(
    *,
    raw_root: str | Path = "data/raw",
    selected_dimensions: tuple[str, ...] | None = None,
) -> tuple[WGISnapshotReference, ...]:
    """Download official WGI dimension ZIP snapshots, reusing matching checksums."""

    dimensions = selected_dimensions or tuple(
        mapping.official_dimension_code for mapping in wgi_mapping_registry()
    )
    snapshots: list[WGISnapshotReference] = []
    timestamp = utc_now()
    for dimension in dimensions:
        dataset = _dataset_for_dimension(dimension)
        metadata, _ = acquire_snapshot(
            request=DownloadRequest(
                provider="world_bank/wgi",
                dataset=dataset.dataset_id,
                raw_root=Path(raw_root),
                source_url=dataset.source_url,
                filename=f"world_bank_wgi_{dimension.lower()}_api_csv.zip",
                download_timestamp=timestamp,
            ),
            dataset=dataset,
            provider_id="world_bank/wgi",
        )
        snapshots.append(
            WGISnapshotReference(
                snapshot_path=metadata.snapshot_path,
                metadata_path=Path(f"{metadata.snapshot_path}.metadata.json"),
                source_url=metadata.source_url,
                checksum_sha256=metadata.checksum_sha256,
                original_filename=metadata.original_filename,
                downloaded_at=metadata.downloaded_at,
                dimension_code=dimension,
            )
        )
    return tuple(sorted(snapshots, key=lambda item: item.dimension_code))


def _dataset_for_dimension(dimension_code: str) -> ProviderDataset:
    mapping = {item.official_dimension_code: item for item in wgi_mapping_registry()}[
        dimension_code
    ]
    return ProviderDataset(
        dataset_id=f"WGI_{dimension_code}",
        title=f"WGI {mapping.canonical_label}",
        source_url=wgi_dimension_download_url(dimension_code),
        description=(
            "Official World Bank Indicators API CSV ZIP for WGI central estimates, "
            "standard errors, source counts, and absolute governance score metadata."
        ),
        license="Creative Commons Attribution 4.0",
        citation="Worldwide Governance Indicators, 2025 Revision, World Bank.",
        publication_date="2026-03-18",
        version="2025 Revision",
        geographic_coverage=GeographicScope(
            codes=["GLOBAL"],
            description="World Bank WGI country and economy coverage.",
        ),
        temporal_coverage=TemporalScope(start=1996, end=2024, label="Annual country-year records"),
        variables=(
            DatasetVariable(
                variable_id=mapping.official_estimate_indicator_id,
                label=mapping.official_title,
                data_type=DataType.FLOAT,
                role=VariableRole.PREDICTOR,
                source_field_name="Value",
            ),
        ),
        units=("country-year", "standard normal governance estimate"),
        frequency="annual",
        format=".zip",
        methodology_reference="https://www.worldbank.org/en/publication/worldwide-governance-indicators/documentation",
    )
