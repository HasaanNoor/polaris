"""Build deterministic UNESCO UIS education panels from local files."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from polaris.harmonization.countries import normalize_country_identifier
from polaris.harmonization.models import GeographicEntityType
from polaris.unesco.catalog import load_country_names, load_indicator_labels, source_checksums
from polaris.unesco.dimensions import (
    age_dimension,
    education_level_dimension,
    is_headline_both_sexes,
    location_dimension,
    sex_dimension,
    wealth_dimension,
)
from polaris.unesco.mappings import mappings_for_indicators, unesco_mapping_registry
from polaris.unesco.models import (
    UNESCODeferredIndicator,
    UNESCOEducationPanel,
    UNESCOEducationQualitySummary,
    UNESCOEducationRecord,
    UNESCOEducationSuitability,
    UNESCOEducationVariableMapping,
    UNESCOIndicatorProfile,
    UNESCOValueProvenance,
)
from polaris.unesco.profiling import load_unesco_rows, profile_candidate_indicators
from polaris.unesco.provenance import deterministic_unesco_panel_id


def default_selected_indicators() -> tuple[str, ...]:
    return tuple(mapping.unesco_indicator_id for mapping in unesco_mapping_registry())


def build_unesco_education_panel(
    *,
    raw_root: str | Path = "data/raw/unesco",
    selected_indicators: tuple[str, ...] | None = None,
) -> UNESCOEducationPanel:
    selected = selected_indicators or default_selected_indicators()
    mappings = tuple(
        sorted(mappings_for_indicators(tuple(selected)), key=lambda m: m.canonical_variable_id)
    )
    labels = load_indicator_labels(raw_root=raw_root)["SDG"]
    country_names = load_country_names(raw_root=raw_root)["SDG"]
    source_path = Path(raw_root) / "SDG" / "SDG_DATA_NATIONAL.csv"
    rows = load_unesco_rows(source_path)
    rows_by_indicator: dict[str, list[tuple[int, dict[str, str]]]] = defaultdict(list)
    for row_number, row in enumerate(rows, start=1):
        if row.get("INDICATOR_ID") in selected:
            rows_by_indicator[str(row["INDICATOR_ID"])].append((row_number, row))
    profiles = profile_candidate_indicators(
        raw_root=raw_root, dataset="SDG", indicator_ids=tuple(selected)
    )
    checksums = source_checksums(raw_root=raw_root)
    data_checksum = checksums["SDG:data"]
    values: dict[tuple[str, int], dict[str, float]] = defaultdict(dict)
    provenance: dict[tuple[str, int], dict[str, UNESCOValueProvenance]] = defaultdict(dict)
    names: dict[str, str] = {}
    contributing: dict[tuple[str, int], set[str]] = defaultdict(set)
    exclusions: Counter[str] = Counter()
    duplicate_findings: list[str] = []

    for mapping in mappings:
        selected_keys: set[tuple[str, int]] = set()
        for row_number, row in rows_by_indicator.get(mapping.unesco_indicator_id, []):
            label = labels[mapping.unesco_indicator_id]
            if not is_headline_both_sexes(mapping.unesco_indicator_id, label):
                exclusions["subgroup_exclusions"] += 1
                continue
            country = normalize_country_identifier(
                row.get("COUNTRY_ID"),
                provider="unesco",
                source_name=country_names.get(str(row.get("COUNTRY_ID"))),
            )
            if country.entity_type is GeographicEntityType.TERRITORY:
                exclusions["territory_exclusions"] += 1
                continue
            if country.entity_type is GeographicEntityType.UNKNOWN:
                exclusions["unknown_entity_exclusions"] += 1
                continue
            if country.entity_type is not GeographicEntityType.SOVEREIGN_COUNTRY:
                exclusions["aggregate_exclusions"] += 1
                continue
            value = _float_or_none(row.get("VALUE"))
            year = _safe_year(row.get("YEAR"))
            if value is None or year is None:
                exclusions["source_missing"] += 1
                continue
            key = (str(country.canonical_code), year)
            if key in selected_keys:
                duplicate_findings.append(
                    f"{mapping.unesco_indicator_id}: duplicate selected row for {key[0]} {key[1]}"
                )
                continue
            selected_keys.add(key)
            names[key[0]] = country.canonical_name or key[0]
            values[key][mapping.canonical_variable_id] = value
            provenance[key][mapping.canonical_variable_id] = _value_provenance(
                row=row,
                row_number=row_number,
                mapping=mapping,
                source_path=source_path,
                source_checksum=data_checksum,
                label=label,
            )
            contributing[key].add(mapping.unesco_indicator_id)

    records = tuple(
        UNESCOEducationRecord(
            canonical_country_code=code,
            canonical_country_name=names.get(code, code),
            year=year,
            values=dict(sorted(values[(code, year)].items())),
            value_provenance=dict(sorted(provenance[(code, year)].items())),
            contributing_unesco_indicators=tuple(sorted(contributing[(code, year)])),
        )
        for code, year in sorted(values)
    )
    deferred = _deferred_indicators(
        labels=labels, integrated={m.unesco_indicator_id for m in mappings}
    )
    quality = _quality_summary(
        mappings=mappings,
        records=records,
        deferred=deferred,
        profiles=profiles,
        exclusions=exclusions,
        duplicate_findings=tuple(sorted(duplicate_findings)),
    )
    identity_payload = {
        "selected": [mapping.model_dump(mode="json") for mapping in mappings],
        "source_checksums": checksums,
        "geographic_rules": (
            "Phase 12 exact ISO-3 normalization; aggregates and territories excluded"
        ),
        "schema_version": "1.0.0",
    }
    return UNESCOEducationPanel(
        panel_id=deterministic_unesco_panel_id(payload=identity_payload),
        integrated_variable_catalog=mappings,
        records=records,
        value_provenance=tuple(
            prov for record in records for _, prov in sorted(record.value_provenance.items())
        ),
        indicator_profiles=tuple(sorted(profiles, key=lambda profile: profile.unesco_indicator_id)),
        quality_summary=quality,
        findings=tuple(sorted(duplicate_findings)),
        deferred_indicator_registry=deferred,
        source_checksums=checksums,
    )


def _value_provenance(
    *,
    row: dict[str, str],
    row_number: int,
    mapping: UNESCOEducationVariableMapping,
    source_path: Path,
    source_checksum: str,
    label: str,
) -> UNESCOValueProvenance:
    return UNESCOValueProvenance(
        canonical_variable_id=mapping.canonical_variable_id,
        unesco_indicator_id=mapping.unesco_indicator_id,
        official_title=mapping.official_title,
        source_dataset=mapping.source_dataset,
        source_file=str(source_path),
        source_checksum=source_checksum,
        source_row=row_number,
        original_country_identifier=str(row["COUNTRY_ID"]),
        original_year=int(row["YEAR"]),
        original_value=row.get("VALUE"),
        normalized_value=float(row["VALUE"]),
        unit=mapping.unit,
        sex=sex_dimension(mapping.unesco_indicator_id, label),
        age_cohort=age_dimension(mapping.unesco_indicator_id, label),
        education_level=education_level_dimension(mapping.unesco_indicator_id, label),
        location_dimension=location_dimension(mapping.unesco_indicator_id, label),
        estimate_status="modelled data" if "modelled data" in label.casefold() else None,
        applied_filters=("explicit both-sexes headline indicator; no subgroup averaging",),
        source_manifest_reference="data/raw/unesco/SDG/SDG_LABEL.csv",
    )


def _deferred_indicators(
    *,
    labels: dict[str, str],
    integrated: set[str],
) -> tuple[UNESCODeferredIndicator, ...]:
    deferred: list[UNESCODeferredIndicator] = []
    education_terms = (
        "literacy",
        "completion",
        "enrolment",
        "attendance",
        "out-of-school",
        "teacher",
        "education",
        "proficiency",
        "attainment",
        "parity",
    )
    for indicator_id, title in sorted(labels.items()):
        if indicator_id in integrated:
            continue
        if not any(term in title.casefold() for term in education_terms):
            continue
        dimensions = tuple(
            item
            for item in (
                sex_dimension(indicator_id, title),
                age_dimension(indicator_id, title),
                education_level_dimension(indicator_id, title),
                location_dimension(indicator_id, title),
                wealth_dimension(indicator_id, title),
            )
            if item is not None
        )
        sex = sex_dimension(indicator_id, title)
        reason = "not selected for the reviewed default Phase 17 country-year panel"
        suitability = UNESCOEducationSuitability.MEDIUM
        if sex in {"female", "male"}:
            reason = "sex-specific indicator; sexes are not manually averaged"
            suitability = UNESCOEducationSuitability.LOW
        elif location_dimension(indicator_id, title) or wealth_dimension(indicator_id, title):
            reason = "subgrouped indicator; subgroup values are not collapsed"
            suitability = UNESCOEducationSuitability.LOW
        elif "proficiency" in title.casefold():
            reason = "learning outcome retained for later assessment-dimension review"
            suitability = UNESCOEducationSuitability.MEDIUM
        deferred.append(
            UNESCODeferredIndicator(
                source_dataset="SDG",
                unesco_indicator_id=indicator_id,
                title=title,
                suitability=suitability,
                reason_deferred=reason,
                problematic_dimensions=dimensions,
                future_work_needed=(
                    "Review definition, dimensions, and analytical role before promotion."
                ),
                potential_analytical_use="Education equity or learning-outcome analysis",
            )
        )
    return tuple(deferred)


def _quality_summary(
    *,
    mappings: tuple[UNESCOEducationVariableMapping, ...],
    records: tuple[UNESCOEducationRecord, ...],
    deferred: tuple[UNESCODeferredIndicator, ...],
    profiles: tuple[UNESCOIndicatorProfile, ...],
    exclusions: Counter[str],
    duplicate_findings: tuple[str, ...],
) -> UNESCOEducationQualitySummary:
    years = [record.year for record in records]
    variable_ids = tuple(mapping.canonical_variable_id for mapping in mappings)
    return UNESCOEducationQualitySummary(
        candidate_indicator_count=len(mappings) + len(deferred),
        integrated_indicator_count=len(mappings),
        deferred_indicator_count=len(deferred),
        country_count=len({record.canonical_country_code for record in records}),
        year_range=(min(years), max(years)) if years else None,
        country_year_record_count=len(records),
        missingness_by_variable={
            variable_id: {
                "observed": sum(1 for record in records if variable_id in record.values),
                "country_year_absent": sum(
                    1 for record in records if variable_id not in record.values
                ),
            }
            for variable_id in variable_ids
        },
        aggregate_exclusions=exclusions["aggregate_exclusions"],
        sex_specific_exclusions=exclusions["sex_specific_exclusions"],
        subgroup_exclusions=exclusions["subgroup_exclusions"],
        territory_exclusions=exclusions["territory_exclusions"],
        unknown_entity_exclusions=exclusions["unknown_entity_exclusions"],
        duplicate_findings=duplicate_findings,
        source_coverage={
            profile.unesco_indicator_id: profile.country_coverage for profile in profiles
        },
        analysis_ready=bool(records) and not duplicate_findings,
    )


def _float_or_none(value: object) -> float | None:
    if value in {None, ""}:
        return None
    return float(str(value))


def _safe_year(value: object) -> int | None:
    text = "" if value is None else str(value).strip()
    return int(text) if text.isdigit() and len(text) == 4 else None
