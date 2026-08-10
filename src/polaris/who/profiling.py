"""Schema profiling for local WHO GHO indicator snapshots."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from polaris.harmonization.countries import normalize_country_identifier
from polaris.harmonization.models import GeographicEntityType
from polaris.ingestion.loader import calculate_sha256
from polaris.who.errors import WHOChecksumError
from polaris.who.models import WHOIndicatorProfile, WHOSuitability

NUMERIC_FIELDS = ("NumericValue", "Low", "High")
DIMENSION_FIELDS = ("Dim1", "Dim2", "Dim3", "DataSourceDim")
STATUS_FIELDS = ("DataSourceDim",)


def load_who_rows(source_path: str | Path) -> tuple[dict[str, Any], ...]:
    """Read local OData JSON rows from a WHO snapshot."""

    path = Path(source_path)
    with path.open(encoding="utf-8") as file:
        payload = json.load(file)
    rows = payload.get("value", []) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return ()
    return tuple(row for row in rows if isinstance(row, dict))


def profile_who_indicator(
    *,
    target: dict[str, Any],
    catalog_path: str | Path | None = None,
    validate_checksum: bool = True,
) -> WHOIndicatorProfile:
    """Build an observed schema profile for one catalog target."""

    source_path = Path(target["local_snapshot_path"])
    expected_checksum = str(target.get("sha256") or "").lower()
    actual_checksum = calculate_sha256(source_path)
    if validate_checksum and expected_checksum and actual_checksum != expected_checksum:
        raise WHOChecksumError(
            f"{source_path}: expected {expected_checksum}, observed {actual_checksum}"
        )

    rows = load_who_rows(source_path)
    keys = set().union(*(row.keys() for row in rows)) if rows else set()
    numeric_fields = tuple(field for field in NUMERIC_FIELDS if field in keys)
    country_field = "SpatialDim" if "SpatialDim" in keys else None
    temporal_field = "TimeDim" if "TimeDim" in keys else None

    null_counts = {
        key: sum(1 for row in rows if row.get(key) is None or row.get(key) == "")
        for key in sorted(keys)
    }
    dim_values: dict[str, set[str]] = defaultdict(set)
    sex_values: set[str] = set()
    age_values: set[str] = set()
    status_values: set[str] = set()
    for row in rows:
        for field in DIMENSION_FIELDS:
            value = row.get(field)
            if value is not None:
                dim_values[field].add(str(value))
                if str(value).startswith("SEX_"):
                    sex_values.add(str(value))
                if str(value).startswith("AGEGROUP_"):
                    age_values.add(str(value))
        for field in STATUS_FIELDS:
            value = row.get(field)
            if value is not None:
                status_values.add(str(value))

    country_codes: set[str] = set()
    aggregates = territories = unknown = 0
    for row in rows:
        spatial_type = row.get("SpatialDimType")
        spatial = row.get("SpatialDim")
        if spatial_type == "COUNTRY":
            country = normalize_country_identifier(spatial, provider="who")
            if country.entity_type is GeographicEntityType.SOVEREIGN_COUNTRY:
                country_codes.add(str(country.canonical_code or spatial))
            elif country.entity_type is GeographicEntityType.TERRITORY:
                territories += 1
            elif country.entity_type is GeographicEntityType.UNKNOWN:
                unknown += 1
        else:
            aggregates += 1

    years = sorted(int(row["TimeDim"]) for row in rows if isinstance(row.get("TimeDim"), int))
    key_counter = Counter(
        (row.get("SpatialDim"), row.get("TimeDim"))
        for row in rows
        if row.get("SpatialDimType") == "COUNTRY"
    )
    duplicate_count = sum(1 for count in key_counter.values() if count > 1)
    duplicate_findings = (
        (f"{duplicate_count} country-year keys duplicate before reviewed dimension filters",)
        if duplicate_count
        else ()
    )
    schema_findings: list[str] = []
    if country_field is None:
        schema_findings.append("no SpatialDim geographic field observed")
    if temporal_field is None:
        schema_findings.append("no TimeDim temporal field observed")
    if "NumericValue" not in numeric_fields:
        schema_findings.append("no NumericValue field observed")

    other_dimensions = {
        field: tuple(sorted(values))
        for field, values in sorted(dim_values.items())
        if field not in {"Dim1", "Dim2"} or not (values <= sex_values or values <= age_values)
    }
    return WHOIndicatorProfile(
        who_indicator_id=target["selected_who_indicator_id"],
        official_title=target.get("selected_title") or target["selected_who_indicator_id"],
        conceptual_target=target.get("conceptual_target") or target["selected_who_indicator_id"],
        source_path=str(source_path),
        source_checksum=actual_checksum,
        checksum_validated=not expected_checksum or actual_checksum == expected_checksum,
        row_count=len(rows),
        geographic_field=country_field,
        temporal_field=temporal_field,
        numeric_value_fields=numeric_fields,
        sex_dimensions=tuple(sorted(sex_values)),
        age_dimensions=tuple(sorted(age_values)),
        estimate_status_dimensions=tuple(sorted(status_values)),
        other_dimensions=other_dimensions,
        units_observed=(),
        country_count=len(country_codes),
        aggregate_count=aggregates,
        territory_count=territories,
        unknown_entity_count=unknown,
        year_range=(years[0], years[-1]) if years else None,
        null_counts=null_counts,
        duplicate_key_findings=duplicate_findings,
        schema_findings=tuple(schema_findings),
        suitability_classification=WHOSuitability(target.get("integration_suitability", "LOW")),
    )


def profile_downloaded_who_indicators(
    *,
    catalog: dict[str, Any],
    validate_checksum: bool = True,
) -> tuple[WHOIndicatorProfile, ...]:
    """Profile every downloaded target in catalog order."""

    profiles = []
    for target in catalog.get("targets", []):
        if target.get("local_snapshot_path") and target.get("selected_who_indicator_id"):
            profiles.append(
                profile_who_indicator(target=target, validate_checksum=validate_checksum)
            )
    return tuple(profiles)
