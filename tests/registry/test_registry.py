import pytest

from polaris.registry import DatasetNotFoundError, DatasetRegistry, DuplicateDatasetError
from polaris.schemas.dataset import DatasetManifest


def test_empty_registry() -> None:
    registry = DatasetRegistry()

    assert registry.count == 0
    assert len(registry) == 0
    assert registry.list_all() == ()


def test_register_manifest(world_bank_manifest: DatasetManifest) -> None:
    registry = DatasetRegistry()

    registry.register(world_bank_manifest)

    assert registry.count == 1
    assert registry.contains("world_bank_wdi_illustrative")


def test_register_many_preserves_order(
    world_bank_manifest: DatasetManifest,
    who_manifest: DatasetManifest,
) -> None:
    registry = DatasetRegistry([who_manifest])

    registry.register_many([world_bank_manifest])

    assert [manifest.dataset_id for manifest in registry] == [
        "who_gho_illustrative",
        "world_bank_wdi_illustrative",
    ]


def test_duplicate_identifier_rejected(world_bank_manifest: DatasetManifest) -> None:
    registry = DatasetRegistry([world_bank_manifest])

    with pytest.raises(DuplicateDatasetError, match="world_bank_wdi_illustrative"):
        registry.register(world_bank_manifest)


def test_retrieval(world_bank_manifest: DatasetManifest) -> None:
    registry = DatasetRegistry([world_bank_manifest])

    assert registry.get("world_bank_wdi_illustrative") == world_bank_manifest


def test_missing_identifier() -> None:
    registry = DatasetRegistry()

    with pytest.raises(DatasetNotFoundError, match="missing"):
        registry.get("missing")


def test_internal_collection_protection(world_bank_manifest: DatasetManifest) -> None:
    registry = DatasetRegistry([world_bank_manifest])
    listed = registry.list_all()

    listed += (world_bank_manifest,)

    assert registry.count == 1


def test_rejects_non_manifest() -> None:
    registry = DatasetRegistry()

    with pytest.raises(Exception, match="DatasetManifest"):
        registry.register(object())  # type: ignore[arg-type]
