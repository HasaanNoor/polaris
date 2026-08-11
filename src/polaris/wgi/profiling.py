"""WGI source schema profiling."""

from __future__ import annotations

import csv
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from polaris.harmonization.countries import normalize_country_identifier
from polaris.harmonization.models import GeographicEntityType
from polaris.ingestion.loader import calculate_sha256
from polaris.providers.base import SnapshotMetadata
from polaris.wgi.errors import WGISchemaError, WGISourceValidationError
from polaris.wgi.mappings import wgi_indicator_ids
from polaris.wgi.models import WGIRow, WGISchemaProfile, WGISnapshotReference


def discover_wgi_snapshots(raw_root: str | Path = "data/raw") -> tuple[WGISnapshotReference, ...]:
    """Discover local WGI ZIP snapshots under data/raw/world_bank/wgi."""

    directory = Path(raw_root) / "world_bank" / "wgi"
    snapshots: list[WGISnapshotReference] = []
    for metadata_path in sorted(directory.glob("*.metadata.json")):
        try:
            metadata = SnapshotMetadata.model_validate_json(
                metadata_path.read_text(encoding="utf-8")
            )
        except (OSError, ValidationError, ValueError):
            continue
        dimension = _dimension_from_name(metadata.original_filename)
        if dimension is None:
            dimension = _dimension_from_name(metadata.dataset_id)
        if dimension is None:
            continue
        snapshots.append(
            WGISnapshotReference(
                snapshot_path=metadata.snapshot_path,
                metadata_path=metadata_path,
                source_url=metadata.source_url,
                checksum_sha256=metadata.checksum_sha256,
                original_filename=metadata.original_filename,
                downloaded_at=metadata.downloaded_at,
                dimension_code=dimension,
            )
        )
    return tuple(sorted(snapshots, key=lambda item: item.dimension_code))


def load_wgi_rows(
    *,
    snapshots: tuple[WGISnapshotReference, ...],
) -> tuple[WGIRow, ...]:
    """Load WGI list-format CSV rows from official API ZIP snapshots."""

    rows: list[WGIRow] = []
    allowed = set(wgi_indicator_ids())
    for snapshot in snapshots:
        checksum = calculate_sha256(snapshot.snapshot_path)
        if checksum != snapshot.checksum_sha256:
            raise WGISourceValidationError(f"checksum mismatch for {snapshot.snapshot_path}")
        with zipfile.ZipFile(snapshot.snapshot_path) as archive:
            data_name = _data_csv_name(archive)
            text = archive.read(data_name).decode("utf-8-sig")
        header_index, metadata = _header_index_and_metadata(text.splitlines())
        reader = csv.DictReader(text.splitlines()[header_index:])
        required = {
            "Country Name",
            "Country Code",
            "Indicator Name",
            "Indicator Code",
            "Year",
            "Value",
        }
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise WGISchemaError(f"{snapshot.snapshot_path}: WGI API CSV columns missing")
        for offset, row in enumerate(reader, start=header_index + 2):
            indicator = str(row["Indicator Code"]).strip()
            if indicator not in allowed:
                continue
            year = int(str(row["Year"]).strip())
            rows.append(
                WGIRow(
                    source_path=str(snapshot.snapshot_path),
                    source_checksum=checksum,
                    source_row=offset,
                    data_source=metadata.get("Data Source", "Worldwide Governance Indicators"),
                    last_updated_date=metadata.get("Last Updated Date"),
                    country_name=str(row["Country Name"]).strip(),
                    country_code=str(row["Country Code"]).strip(),
                    indicator_name=str(row["Indicator Name"]).strip(),
                    indicator_code=indicator,
                    year=year,
                    value=_float_or_none(row["Value"]),
                )
            )
    return tuple(sorted(rows, key=lambda item: (item.indicator_code, item.country_code, item.year)))


def profile_wgi_schema(*, snapshots: tuple[WGISnapshotReference, ...]) -> WGISchemaProfile:
    """Profile actual WGI source rows and key fields."""

    rows = load_wgi_rows(snapshots=snapshots)
    entity_counts: Counter[str] = Counter()
    missingness: Counter[str] = Counter()
    duplicate_counter: Counter[tuple[str, int, str]] = Counter()
    checksums = {str(snapshot.snapshot_path): snapshot.checksum_sha256 for snapshot in snapshots}
    for row in rows:
        country = normalize_country_identifier(
            row.country_code,
            provider="world_bank",
            source_name=row.country_name,
        )
        entity_counts[country.entity_type.value] += 1
        if row.value is None:
            missingness[row.indicator_code] += 1
        duplicate_counter[(row.country_code, row.year, row.indicator_code)] += 1
    years = sorted({row.year for row in rows})
    duplicate_findings = tuple(
        f"{country_code} {year} {indicator}: {count} rows"
        for (country_code, year, indicator), count in sorted(duplicate_counter.items())
        if count > 1
    )
    return WGISchemaProfile(
        source_paths=tuple(sorted(checksums)),
        source_checksums=checksums,
        checksum_validated=True,
        row_count=len(rows),
        standard_error_indicators=tuple(
            sorted(i for i in wgi_indicator_ids() if i.endswith(".SE"))
        ),
        percentile_rank_indicators=(),
        confidence_bound_indicators=tuple(
            sorted(i for i in wgi_indicator_ids() if i.endswith((".SC_LB", ".SC_UB")))
        ),
        source_count_indicators=tuple(sorted(i for i in wgi_indicator_ids() if i.endswith(".SR"))),
        country_count=len(_sovereign_country_codes(rows)),
        aggregate_count=(
            entity_counts[GeographicEntityType.REGION.value]
            + entity_counts[GeographicEntityType.INCOME_GROUP.value]
            + entity_counts[GeographicEntityType.GLOBAL_AGGREGATE.value]
        ),
        territory_count=entity_counts[GeographicEntityType.TERRITORY.value],
        unknown_entity_count=entity_counts[GeographicEntityType.UNKNOWN.value],
        year_range=(years[0], years[-1]) if years else None,
        missingness_by_indicator=dict(sorted(missingness.items())),
        duplicate_key_findings=duplicate_findings,
        schema_findings=(),
    )


def _data_csv_name(archive: zipfile.ZipFile) -> str:
    candidates = [
        name
        for name in archive.namelist()
        if name.endswith(".csv") and Path(name).name.startswith("API_Download")
    ]
    if len(candidates) != 1:
        raise WGISchemaError("WGI ZIP must contain one API_Download CSV")
    return candidates[0]


def _header_index_and_metadata(lines: list[str]) -> tuple[int, dict[str, str]]:
    metadata: dict[str, str] = {}
    for index, line in enumerate(lines):
        if line.startswith('"Country Name"') or line.startswith("Country Name"):
            return index, metadata
        if not line.strip():
            continue
        parsed = next(csv.reader([line]))
        if len(parsed) >= 2:
            metadata[parsed[0]] = parsed[1]
    raise WGISchemaError("WGI API CSV header not found")


def _float_or_none(value: Any) -> float | None:
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    return float(text)


def _dimension_from_name(value: str) -> str | None:
    upper = value.upper()
    for dimension in ("VA", "PV", "GE", "RQ", "RL", "CC"):
        if f"_{dimension}" in upper or upper.endswith(dimension):
            return dimension
    return None


def _sovereign_country_codes(rows: tuple[WGIRow, ...]) -> set[str | None]:
    codes = set()
    for row in rows:
        country = normalize_country_identifier(
            row.country_code,
            provider="world_bank",
            source_name=row.country_name,
        )
        if country.entity_type is GeographicEntityType.SOVEREIGN_COUNTRY:
            codes.add(country.canonical_code)
    return codes
