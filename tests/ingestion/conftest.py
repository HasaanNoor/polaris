from __future__ import annotations

import pytest

from polaris.registry import DatasetRegistry
from polaris.schemas.dataset import DatasetManifest
from tests.registry.helpers import catalog_manifest


@pytest.fixture
def world_bank_manifest() -> DatasetManifest:
    return catalog_manifest("world_bank_wdi.json")


@pytest.fixture
def who_manifest() -> DatasetManifest:
    return catalog_manifest("who_gho.json")


@pytest.fixture
def unesco_manifest() -> DatasetManifest:
    return catalog_manifest("unesco_uis.json")


@pytest.fixture
def registry(
    world_bank_manifest: DatasetManifest,
    who_manifest: DatasetManifest,
    unesco_manifest: DatasetManifest,
) -> DatasetRegistry:
    return DatasetRegistry([world_bank_manifest, who_manifest, unesco_manifest])
