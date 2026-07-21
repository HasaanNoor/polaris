from pathlib import Path

import pytest

from polaris.registry import (
    ManifestLoadError,
    ManifestValidationError,
    load_manifest,
    load_manifests,
    load_registry,
)
from polaris.schemas.dataset import DatasetManifest
from tests.registry.helpers import CATALOG_DIR, write_manifest


def test_load_valid_single_manifest() -> None:
    manifest = load_manifest(CATALOG_DIR / "world_bank_wdi.json")

    assert manifest.dataset_id == "world_bank_wdi_illustrative"


def test_load_valid_directory() -> None:
    manifests = load_manifests(CATALOG_DIR)

    assert len(manifests) == 3
    assert all(isinstance(manifest, DatasetManifest) for manifest in manifests)


def test_load_directory_is_deterministic() -> None:
    manifests = load_manifests(CATALOG_DIR)

    assert [manifest.dataset_id for manifest in manifests] == [
        "unesco_uis_illustrative",
        "who_gho_illustrative",
        "world_bank_wdi_illustrative",
    ]


def test_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(ManifestLoadError, match="bad.json"):
        load_manifest(path)


def test_schema_invalid_json(tmp_path: Path, manifest_data: dict) -> None:
    path = tmp_path / "invalid.json"
    del manifest_data["dataset_id"]
    write_manifest(path, manifest_data)

    with pytest.raises(ManifestValidationError, match="invalid.json"):
        load_manifest(path)


def test_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"

    with pytest.raises(ManifestLoadError, match="missing.json"):
        load_manifest(path)


def test_missing_directory(tmp_path: Path) -> None:
    path = tmp_path / "missing"

    with pytest.raises(ManifestLoadError, match="missing"):
        load_manifests(path)


def test_empty_directory_behavior(tmp_path: Path) -> None:
    assert load_manifests(tmp_path) == ()
    assert load_registry(tmp_path).count == 0


def test_unrelated_files_are_ignored(tmp_path: Path, manifest_data: dict) -> None:
    write_manifest(tmp_path / "manifest.json", manifest_data)
    (tmp_path / "notes.md").write_text("not a manifest", encoding="utf-8")

    assert len(load_manifests(tmp_path)) == 1


def test_load_registry_from_directory() -> None:
    registry = load_registry(CATALOG_DIR)

    assert registry.count == 3
