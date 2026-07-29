"""Snapshot cache discovery utilities."""

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from polaris.providers.base import DatasetSnapshot, SnapshotMetadata


def provider_raw_dir(raw_root: str | Path, provider_id: str) -> Path:
    return Path(raw_root) / provider_id


def snapshot_metadata_path(snapshot_path: str | Path) -> Path:
    return Path(f"{snapshot_path}.metadata.json")


def find_snapshot_by_checksum(
    raw_root: str | Path,
    provider_id: str,
    checksum: str,
) -> DatasetSnapshot | None:
    """Return the first snapshot metadata record matching a checksum."""

    directory = provider_raw_dir(raw_root, provider_id)
    if not directory.exists():
        return None

    for path in sorted(directory.glob("*.metadata.json"), key=lambda item: item.name):
        try:
            payload: Any = json.loads(path.read_text(encoding="utf-8"))
            metadata = SnapshotMetadata.model_validate(payload)
        except (OSError, JSONDecodeError, ValidationError):
            continue
        if metadata.checksum_sha256 == checksum.lower():
            return DatasetSnapshot(metadata=metadata, metadata_path=path)
    return None


def write_snapshot_metadata(metadata: SnapshotMetadata, path: str | Path) -> None:
    metadata_path = Path(path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        metadata.model_dump_json(indent=2),
        encoding="utf-8",
    )
