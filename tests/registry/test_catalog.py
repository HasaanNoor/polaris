from polaris.registry import load_manifests, load_registry
from tests.registry.helpers import CATALOG_DIR


def test_example_catalog_loads_completely() -> None:
    manifests = load_manifests(CATALOG_DIR)

    assert len(manifests) == 3


def test_example_catalog_records_are_candidates() -> None:
    registry = load_registry(CATALOG_DIR)

    assert {manifest.status.value for manifest in registry} == {"candidate"}
