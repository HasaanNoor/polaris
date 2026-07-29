"""Illustrative Phase 10 provider acquisition examples.

The examples use local sample CSV files so they can run without network access.
Replace ``source_url`` with a provider download URL when acquiring an official
snapshot for real research.
"""

from pathlib import Path

from polaris.ingestion import IngestionRequest, ingest_dataset
from polaris.providers import default_provider_registry, download_dataset
from polaris.registry import DatasetRegistry

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "data" / "examples"


def download_world_bank_wdi() -> None:
    result = download_dataset(
        provider="world_bank",
        dataset="WDI",
        source_url=(EXAMPLES / "world_bank_wdi_sample.csv").as_uri(),
        raw_root=ROOT / "data" / "raw",
        manifest_root=ROOT / "data" / "manifests",
    )
    print(result.manifest.dataset_id)
    print(result.snapshot.path)


def list_who_datasets() -> None:
    registry = default_provider_registry()
    for dataset in registry.list_datasets("who"):
        print(dataset.dataset_id, dataset.title)


def generate_manifest_and_ingest() -> None:
    result = download_dataset(
        provider="unesco",
        dataset="UIS",
        source_url=(EXAMPLES / "unesco_uis_sample.csv").as_uri(),
        raw_root=ROOT / "data" / "raw",
        manifest_root=ROOT / "data" / "manifests",
    )
    registry = DatasetRegistry([result.manifest])
    ingestion = ingest_dataset(
        registry=registry,
        request=IngestionRequest(
            dataset_id=result.manifest.dataset_id,
            source_path=result.snapshot.path,
            expected_checksum=result.manifest.checksum,
        ),
    )
    print(ingestion.validation_report.analysis_ready)
