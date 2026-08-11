"""Build deterministic WGI governance panels from official local snapshots."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from polaris.harmonization.countries import normalize_country_identifier
from polaris.harmonization.models import GeographicEntityType
from polaris.wgi.mappings import wgi_mapping_registry
from polaris.wgi.models import (
    WGIGovernancePanel,
    WGIGovernanceRecord,
    WGIMissingnessReasonCode,
    WGIPanelQualitySummary,
    WGISnapshotReference,
    WGIValueProvenance,
    WGIVariableMapping,
)
from polaris.wgi.profiling import discover_wgi_snapshots, load_wgi_rows, profile_wgi_schema
from polaris.wgi.provenance import deterministic_wgi_panel_id


def build_wgi_governance_panel(
    *,
    raw_root: str | Path = "data/raw",
    snapshots: tuple[WGISnapshotReference, ...] | None = None,
) -> WGIGovernancePanel:
    """Build an analysis-ready WGI country-year panel without interpolation."""

    selected_snapshots = snapshots or discover_wgi_snapshots(raw_root)
    mappings = tuple(sorted(wgi_mapping_registry(), key=lambda item: item.canonical_variable_id))
    rows = load_wgi_rows(snapshots=selected_snapshots)
    profile = profile_wgi_schema(snapshots=selected_snapshots)
    companion_to_mapping = _companion_to_mapping(mappings)
    cells: dict[tuple[str, int, str], dict[str, object]] = defaultdict(dict)
    row_refs: dict[tuple[str, int, str], dict[str, object]] = defaultdict(dict)
    exclusions: Counter[str] = Counter()
    unmapped: Counter[str] = Counter()
    duplicate_keys: list[str] = []

    for row in rows:
        mapping = companion_to_mapping[row.indicator_code]
        country = normalize_country_identifier(
            row.country_code,
            provider="world_bank",
            source_name=row.country_name,
        )
        if country.entity_type is GeographicEntityType.TERRITORY:
            exclusions["territory"] += 1
            continue
        if country.entity_type in {
            GeographicEntityType.REGION,
            GeographicEntityType.INCOME_GROUP,
            GeographicEntityType.GLOBAL_AGGREGATE,
        }:
            exclusions["aggregate"] += 1
            continue
        if country.entity_type is not GeographicEntityType.SOVEREIGN_COUNTRY:
            unmapped[row.country_code or row.country_name] += 1
            continue
        if row.value is None:
            continue
        key = (country.canonical_code or row.country_code, row.year, mapping.canonical_variable_id)
        role = _role(row.indicator_code)
        if role in cells[key]:
            duplicate_keys.append(f"{key[0]} {key[1]} {key[2]} {role}")
            continue
        cells[key][role] = row.value
        row_refs[key][role] = row

    records = _records(
        cells=cells,
        row_refs=row_refs,
        mappings=mappings,
        duplicate_keys=duplicate_keys,
    )
    quality = _quality_summary(
        mappings=mappings,
        records=records,
        exclusions=exclusions,
        unmapped=unmapped,
        duplicate_keys=duplicate_keys,
    )
    source_checksums = {
        str(snapshot.snapshot_path): snapshot.checksum_sha256 for snapshot in selected_snapshots
    }
    panel_id = deterministic_wgi_panel_id(
        {
            "source_checksums": source_checksums,
            "selected_variables": [m.model_dump(mode="json") for m in mappings],
            "country_rules": "phase12_exact_country_normalization_exclude_aggregates_territories",
            "temporal_rules": "safe_integer_year_no_interpolation",
        }
    )
    provenance = tuple(
        provenance
        for record in records
        for _, provenance in sorted(record.value_provenance.items())
    )
    return WGIGovernancePanel(
        panel_id=panel_id,
        records=records,
        variable_catalog=mappings,
        source_checksums=source_checksums,
        source_metadata=tuple(sorted(selected_snapshots, key=lambda item: item.dimension_code)),
        schema_profile=profile,
        quality_summary=quality,
        findings=tuple(sorted(set(duplicate_keys))),
        provenance=provenance,
    )


def _records(
    *,
    cells: dict[tuple[str, int, str], dict[str, object]],
    row_refs: dict[tuple[str, int, str], dict[str, object]],
    mappings: tuple[WGIVariableMapping, ...],
    duplicate_keys: list[str],
) -> tuple[WGIGovernanceRecord, ...]:
    grouped: dict[tuple[str, int], dict[str, dict[str, object]]] = defaultdict(dict)
    refs: dict[tuple[str, int], dict[str, dict[str, object]]] = defaultdict(dict)
    for (country_code, year, variable), payload in cells.items():
        grouped[(country_code, year)][variable] = payload
        refs[(country_code, year)][variable] = row_refs[(country_code, year, variable)]
    records: list[WGIGovernanceRecord] = []
    variable_ids = tuple(mapping.canonical_variable_id for mapping in mappings)
    for (country_code, year), variables in sorted(grouped.items()):
        country = normalize_country_identifier(country_code, provider="world_bank")
        values: dict[str, float] = {}
        provenance: dict[str, WGIValueProvenance] = {}
        uncertainty: dict[str, dict[str, float | None]] = {}
        contributing: set[str] = set()
        for mapping in mappings:
            payload = variables.get(mapping.canonical_variable_id)
            if payload is None or "estimate" not in payload:
                continue
            value = float(payload["estimate"])
            ref = refs[(country_code, year)][mapping.canonical_variable_id]["estimate"]
            values[mapping.canonical_variable_id] = value
            uncertainty[mapping.canonical_variable_id] = {
                "standard_error": _float(payload.get("standard_error")),
                "governance_score": _float(payload.get("governance_score")),
                "score_lower_bound": _float(payload.get("score_lower_bound")),
                "score_upper_bound": _float(payload.get("score_upper_bound")),
                "percentile_rank": None,
                "number_of_sources": _float(payload.get("source_count")),
            }
            contributing.update(
                [
                    mapping.official_estimate_indicator_id,
                    mapping.standard_error_indicator_id,
                    mapping.source_count_indicator_id,
                    mapping.governance_score_indicator_id,
                    mapping.score_lower_bound_indicator_id,
                    mapping.score_upper_bound_indicator_id,
                ]
            )
            provenance[mapping.canonical_variable_id] = WGIValueProvenance(
                canonical_variable_id=mapping.canonical_variable_id,
                official_wgi_indicator_id=mapping.official_estimate_indicator_id,
                official_title=mapping.official_title,
                source_dataset=mapping.source_dataset,
                source_snapshot=ref.source_path,
                source_checksum=ref.source_checksum,
                source_row=ref.source_row,
                original_country_identifier=ref.country_code,
                original_country_name=ref.country_name,
                original_year=ref.year,
                original_estimate=ref.value,
                normalized_estimate=value,
                standard_error=_float(payload.get("standard_error")),
                governance_score=_float(payload.get("governance_score")),
                score_lower_bound=_float(payload.get("score_lower_bound")),
                score_upper_bound=_float(payload.get("score_upper_bound")),
                percentile_rank=None,
                number_of_sources=_float(payload.get("source_count")),
                retrieval_metadata={
                    "data_source": ref.data_source,
                    "last_updated_date": ref.last_updated_date or "",
                },
            )
        missingness = {
            variable_id: WGIMissingnessReasonCode.COUNTRY_YEAR_ABSENT
            for variable_id in variable_ids
            if variable_id not in values
        }
        records.append(
            WGIGovernanceRecord(
                canonical_country_code=country_code,
                canonical_country_name=country.canonical_name or country_code,
                year=year,
                values=dict(sorted(values.items())),
                value_provenance=dict(sorted(provenance.items())),
                uncertainty_metadata=dict(sorted(uncertainty.items())),
                contributing_wgi_indicators=tuple(sorted(contributing)),
                missingness=missingness,
                findings=tuple(sorted(set(duplicate_keys))),
            )
        )
    return tuple(records)


def _quality_summary(
    *,
    mappings: tuple[WGIVariableMapping, ...],
    records: tuple[WGIGovernanceRecord, ...],
    exclusions: Counter[str],
    unmapped: Counter[str],
    duplicate_keys: list[str],
) -> WGIPanelQualitySummary:
    years = sorted({record.year for record in records})
    missingness = {}
    uncertainty = {}
    coverage = {}
    for mapping in mappings:
        variable = mapping.canonical_variable_id
        missing_counter: Counter[str] = Counter()
        available = 0
        se = score = bounds = sources = 0
        for record in records:
            if variable in record.values:
                available += 1
                meta = record.uncertainty_metadata.get(variable, {})
                se += int(meta.get("standard_error") is not None)
                score += int(meta.get("governance_score") is not None)
                bounds += int(
                    meta.get("score_lower_bound") is not None
                    and meta.get("score_upper_bound") is not None
                )
                sources += int(meta.get("number_of_sources") is not None)
            else:
                reason = record.missingness.get(variable)
                if reason is not None:
                    missing_counter[reason.value] += 1
        missingness[variable] = dict(sorted(missing_counter.items()))
        coverage[variable] = available
        uncertainty[variable] = {
            "standard_error": se,
            "governance_score": score,
            "score_bounds": bounds,
            "number_of_sources": sources,
            "percentile_rank": 0,
        }
    return WGIPanelQualitySummary(
        integrated_variable_count=len(mappings),
        country_count=len({record.canonical_country_code for record in records}),
        year_range=(years[0], years[-1]) if years else None,
        country_year_record_count=len(records),
        missingness_by_variable=missingness,
        aggregate_exclusions=exclusions["aggregate"],
        territory_exclusions=exclusions["territory"],
        unmapped_entities=dict(sorted(unmapped.items())),
        duplicate_keys=tuple(sorted(duplicate_keys)),
        uncertainty_availability=uncertainty,
        source_coverage=dict(sorted(coverage.items())),
        analysis_ready=bool(records) and not duplicate_keys,
    )


def _companion_to_mapping(
    mappings: tuple[WGIVariableMapping, ...],
) -> dict[str, WGIVariableMapping]:
    output = {}
    for mapping in mappings:
        for indicator in (
            mapping.official_estimate_indicator_id,
            mapping.standard_error_indicator_id,
            mapping.source_count_indicator_id,
            mapping.governance_score_indicator_id,
            mapping.score_lower_bound_indicator_id,
            mapping.score_upper_bound_indicator_id,
        ):
            output[indicator] = mapping
    return output


def _role(indicator_code: str) -> str:
    if indicator_code.endswith(".EST"):
        return "estimate"
    if indicator_code.endswith(".SE"):
        return "standard_error"
    if indicator_code.endswith(".SR"):
        return "source_count"
    if indicator_code.endswith(".SC"):
        return "governance_score"
    if indicator_code.endswith(".SC_LB"):
        return "score_lower_bound"
    if indicator_code.endswith(".SC_UB"):
        return "score_upper_bound"
    return "unknown"


def _float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
