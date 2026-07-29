"""Deterministic file acquisition for provider snapshots."""

import shutil
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse

from polaris.ingestion.loader import calculate_sha256, file_size
from polaris.providers.base import DownloadRequest, ProviderDataset, SnapshotMetadata, utc_now
from polaris.providers.cache import (
    find_snapshot_by_checksum,
    provider_raw_dir,
    snapshot_metadata_path,
    write_snapshot_metadata,
)
from polaris.providers.errors import (
    ChecksumValidationError,
    DownloadError,
    EmptyDownloadError,
)


def filename_from_url(source_url: str, fallback: str) -> str:
    parsed = urlparse(source_url)
    name = Path(unquote(parsed.path)).name
    return name or fallback


def acquire_snapshot(
    *,
    request: DownloadRequest,
    dataset: ProviderDataset,
    provider_id: str,
) -> tuple[SnapshotMetadata, bool]:
    """Download or copy a source file into immutable raw snapshot storage."""

    source_url = request.source_url or dataset.source_url
    timestamp = request.download_timestamp or utc_now()
    original_filename = request.filename or filename_from_url(
        source_url,
        f"{dataset.dataset_id}{dataset.format}",
    )
    raw_dir = provider_raw_dir(request.raw_root, provider_id)
    raw_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = raw_dir / f".pending-{dataset.dataset_id}-{timestamp.strftime('%Y%m%d%H%M%S')}"

    try:
        _copy_source(source_url, temporary_path)
    except OSError as exc:
        raise DownloadError(f"{source_url}: unable to acquire dataset: {exc}") from exc

    size = file_size(temporary_path)
    if size == 0:
        temporary_path.unlink(missing_ok=True)
        raise EmptyDownloadError(source_url)

    checksum = calculate_sha256(temporary_path)
    if request.expected_checksum is not None and checksum != request.expected_checksum.lower():
        temporary_path.unlink(missing_ok=True)
        raise ChecksumValidationError(temporary_path, request.expected_checksum, checksum)

    cached = find_snapshot_by_checksum(request.raw_root, provider_id, checksum)
    if cached is not None:
        temporary_path.unlink(missing_ok=True)
        return cached.metadata, True

    destination = raw_dir / _snapshot_filename(
        dataset_id=dataset.dataset_id,
        timestamp=timestamp,
        checksum=checksum,
        original_filename=original_filename,
    )
    temporary_path.replace(destination)
    metadata = SnapshotMetadata(
        provider=provider_id,
        dataset_id=dataset.dataset_id,
        source_url=source_url,
        original_filename=original_filename,
        snapshot_path=destination,
        checksum_sha256=checksum,
        file_size_bytes=size,
        downloaded_at=timestamp,
        format=destination.suffix.lower(),
    )
    write_snapshot_metadata(metadata, snapshot_metadata_path(destination))
    return metadata, False


def _copy_source(source_url: str, destination: Path) -> None:
    parsed = urlparse(source_url)
    if parsed.scheme in {"", "file"}:
        source_path = Path(unquote(parsed.path)) if parsed.scheme == "file" else Path(source_url)
        shutil.copyfile(source_path, destination)
        return

    with urllib.request.urlopen(source_url, timeout=60) as response:
        with destination.open("wb") as file:
            shutil.copyfileobj(response, file)


def _snapshot_filename(
    *,
    dataset_id: str,
    timestamp,
    checksum: str,
    original_filename: str,
) -> str:
    suffix = Path(original_filename).suffix.lower() or ".csv"
    safe_dataset = _safe_name(dataset_id)
    return f"{safe_dataset}-{timestamp.strftime('%Y%m%dT%H%M%SZ')}-{checksum[:12]}{suffix}"


def _safe_name(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "-" for character in value).strip(
        "-"
    )
