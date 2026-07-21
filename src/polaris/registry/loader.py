import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from polaris.registry.errors import ManifestLoadError, ManifestValidationError
from polaris.registry.registry import DatasetRegistry
from polaris.schemas.dataset import DatasetManifest


def load_manifest(path: str | Path) -> DatasetManifest:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise ManifestLoadError(manifest_path, "manifest path does not exist")
    if not manifest_path.is_file():
        raise ManifestLoadError(manifest_path, "manifest path is not a file")

    try:
        with manifest_path.open(encoding="utf-8") as file:
            payload: Any = json.load(file)
    except JSONDecodeError as exc:
        raise ManifestLoadError(manifest_path, f"malformed JSON: {exc.msg}") from exc
    except OSError as exc:
        raise ManifestLoadError(manifest_path, f"unable to read manifest: {exc}") from exc

    try:
        return DatasetManifest.model_validate(payload)
    except ValidationError as exc:
        raise ManifestValidationError(manifest_path, str(exc)) from exc


def load_manifests(directory: str | Path) -> tuple[DatasetManifest, ...]:
    catalog_directory = Path(directory)
    if not catalog_directory.exists():
        raise ManifestLoadError(catalog_directory, "manifest directory does not exist")
    if not catalog_directory.is_dir():
        raise ManifestLoadError(catalog_directory, "manifest path is not a directory")

    manifests = [
        load_manifest(path)
        for path in sorted(catalog_directory.iterdir(), key=lambda item: item.name)
        if path.is_file() and path.suffix == ".json"
    ]
    return tuple(manifests)


def load_registry(directory: str | Path) -> DatasetRegistry:
    return DatasetRegistry(load_manifests(directory))
