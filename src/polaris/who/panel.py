"""Build deterministic curated WHO health panels from local GHO snapshots."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from polaris.harmonization.countries import normalize_country_identifier
from polaris.harmonization.models import GeographicEntityType
from polaris.who.catalog import downloaded_targets, load_who_acquisition_catalog
from polaris.who.dimensions import (
    exclusion_reason,
    is_aggregate_row,
    is_projected_row,
    row_matches_mapping,
)
from polaris.who.mappings import mappings_for_indicators, who_mapping_registry
from polaris.who.models import (
    WHODeferredIndicator,
    WHOHealthPanel,
    WHOHealthRecord,
    WHOIndicatorProfile,
    WHOMissingnessReasonCode,
    WHOPanelQualitySummary,
    WHOSuitability,
    WHOValueProvenance,
    WHOVariableMapping,
)
from polaris.who.profiling import load_who_rows, profile_who_indicator
from polaris.who.provenance import deterministic_who_panel_id


def default_selected_indicators(catalog: dict[str, Any]) -> tuple[str, ...]:
    """Select reviewed downloaded indicators for the default Phase 15 panel."""

    downloaded = {target.get("selected_who_indicator_id") for target in downloaded_targets(catalog)}
    return tuple(
        mapping.who_indicator_id
        for mapping in who_mapping_registry()
        if mapping.who_indicator_id in downloaded
    )


def build_who_health_panel(
    *,
    catalog_path: str | Path,
    selected_indicators: tuple[str, ...] | None = None,
) -> WHOHealthPanel:
    """Build the reviewed WHO country-year panel from already downloaded snapshots."""

    catalog = load_who_acquisition_catalog(catalog_path)
    selected = selected_indicators or default_selected_indicators(catalog)
    mappings = tuple(
        sorted(
            mappings_for_indicators(tuple(selected)),
            key=lambda item: item.canonical_variable_id,
        )
    )
    targets = {
        target["selected_who_indicator_id"]: target for target in downloaded_targets(catalog)
    }
    profiles: list[WHOIndicatorProfile] = []
    values_by_key: dict[tuple[str, int], dict[str, float]] = defaultdict(dict)
    provenance_by_key: dict[tuple[str, int], dict[str, WHOValueProvenance]] = defaultdict(dict)
    findings_by_key: dict[tuple[str, int], list[str]] = defaultdict(list)
    contributing_by_key: dict[tuple[str, int], set[str]] = defaultdict(set)
    duplicate_findings: list[str] = []
    unresolved_schema_issues: list[str] = []
    source_checksums: dict[str, str] = {}
    exclusion_counts: Counter[str] = Counter()
    selected_variable_ids = tuple(mapping.canonical_variable_id for mapping in mappings)

    for mapping in mappings:
        target = targets.get(mapping.who_indicator_id)
        if target is None:
            unresolved_schema_issues.append(
                f"{mapping.who_indicator_id}: downloaded snapshot missing"
            )
            continue
        profile = profile_who_indicator(target=target)
        profiles.append(profile)
        source_checksums[mapping.who_indicator_id] = profile.source_checksum
        if profile.geographic_field != mapping.country_field:
            unresolved_schema_issues.append(
                f"{mapping.who_indicator_id}: geographic field mismatch"
            )
            continue
        if profile.temporal_field != mapping.year_field:
            unresolved_schema_issues.append(f"{mapping.who_indicator_id}: temporal field mismatch")
            continue
        if mapping.preferred_numeric_source_field not in profile.numeric_value_fields:
            unresolved_schema_issues.append(
                f"{mapping.who_indicator_id}: numeric field "
                f"{mapping.preferred_numeric_source_field} absent"
            )
            continue

        selected_rows: dict[tuple[str, int], tuple[int, dict[str, Any]]] = {}
        rows = load_who_rows(profile.source_path)
        for row_index, row in enumerate(rows, start=1):
            if is_aggregate_row(row):
                exclusion_counts[WHOMissingnessReasonCode.AGGREGATE_ROW_EXCLUDED.value] += 1
            elif row.get("SpatialDimType") == "COUNTRY":
                for rule in mapping.required_dimension_filters:
                    value = row.get(rule.field)
                    if value not in rule.allowed_values:
                        if isinstance(value, str) and value.startswith("SEX_"):
                            exclusion_counts["sex_specific_rows_excluded"] += 1
                        elif isinstance(value, str) and value.startswith("AGEGROUP_"):
                            exclusion_counts["age_specific_rows_excluded"] += 1
                        else:
                            exclusion_counts[exclusion_reason(row, mapping).value] += 1
                        break
            if is_projected_row(row, mapping.who_indicator_id):
                exclusion_counts[WHOMissingnessReasonCode.PROJECTED_ROW_EXCLUDED.value] += 1
            if not row_matches_mapping(row, mapping):
                continue
            country = normalize_country_identifier(row.get(mapping.country_field), provider="who")
            if country.entity_type is GeographicEntityType.TERRITORY:
                exclusion_counts["territory_exclusions"] += 1
                continue
            if country.entity_type is GeographicEntityType.UNKNOWN:
                exclusion_counts["unknown_entity_exclusions"] += 1
                continue
            if country.entity_type is not GeographicEntityType.SOVEREIGN_COUNTRY:
                exclusion_counts[WHOMissingnessReasonCode.AGGREGATE_ROW_EXCLUDED.value] += 1
                continue
            raw_value = row.get(mapping.preferred_numeric_source_field)
            if raw_value is None:
                exclusion_counts[WHOMissingnessReasonCode.SOURCE_VALUE_MISSING.value] += 1
                continue
            key = (
                country.canonical_code or str(row[mapping.country_field]),
                int(row[mapping.year_field]),
            )
            if key in selected_rows:
                duplicate_findings.append(
                    f"{mapping.who_indicator_id}: duplicate selected row for {key[0]} {key[1]}"
                )
                continue
            selected_rows[key] = (row_index, row)
            country_name = country.canonical_name or key[0]
            values_by_key[key][mapping.canonical_variable_id] = float(raw_value)
            provenance_by_key[key][mapping.canonical_variable_id] = _provenance(
                row=row,
                row_index=row_index,
                mapping=mapping,
                profile=profile,
                catalog_path=catalog_path,
            )
            contributing_by_key[key].add(mapping.who_indicator_id)
            if country_name == key[0]:
                findings_by_key[key].append(
                    "country name retained as ISO-3 code; no fuzzy matching"
                )

    records = _records(
        values_by_key=values_by_key,
        provenance_by_key=provenance_by_key,
        contributing_by_key=contributing_by_key,
        findings_by_key=findings_by_key,
        selected_variable_ids=selected_variable_ids,
    )
    deferred = _deferred_indicators(
        catalog=catalog,
        integrated_indicator_ids={mapping.who_indicator_id for mapping in mappings}
        - {issue.split(":", 1)[0] for issue in unresolved_schema_issues},
    )
    quality = _quality_summary(
        mappings=mappings,
        records=records,
        deferred=deferred,
        duplicate_findings=tuple(sorted(duplicate_findings)),
        unresolved_schema_issues=tuple(sorted(unresolved_schema_issues)),
        exclusion_counts=exclusion_counts,
    )
    identity_payload = {
        "selected": [mapping.model_dump(mode="json") for mapping in mappings],
        "source_checksums": source_checksums,
        "quality_scope": {
            "countries": sorted({record.canonical_country_code for record in records}),
            "years": sorted({record.year for record in records}),
        },
    }
    return WHOHealthPanel(
        panel_id=deterministic_who_panel_id(payload=identity_payload),
        selected_indicator_definitions=mappings,
        records=records,
        value_provenance=tuple(
            provenance
            for record in records
            for _, provenance in sorted(record.value_provenance.items())
        ),
        indicator_profiles=tuple(sorted(profiles, key=lambda item: item.who_indicator_id)),
        quality_summary=quality,
        findings=tuple(sorted(set(unresolved_schema_issues + duplicate_findings))),
        deferred_indicators=deferred,
        source_checksums=source_checksums,
    )


def _provenance(
    *,
    row: dict[str, Any],
    row_index: int,
    mapping: WHOVariableMapping,
    profile: WHOIndicatorProfile,
    catalog_path: str | Path,
) -> WHOValueProvenance:
    rule_text = tuple(
        f"{rule.field} in {tuple(rule.allowed_values)}: {rule.reason}"
        for rule in mapping.required_dimension_filters
    )
    return WHOValueProvenance(
        who_indicator_id=mapping.who_indicator_id,
        official_title=profile.official_title,
        canonical_variable_id=mapping.canonical_variable_id,
        source_file=profile.source_path,
        source_checksum=profile.source_checksum,
        source_row=row_index,
        source_geographic_identifier=str(row[mapping.country_field]),
        source_year=int(row[mapping.year_field]),
        source_value=row.get("Value"),
        normalized_numeric_value=float(row[mapping.preferred_numeric_source_field]),
        unit=mapping.unit,
        sex_dimension=_dimension_value(row, "SEX_"),
        age_dimension=_dimension_value(row, "AGEGROUP_"),
        estimate_model_dimension=row.get("DataSourceDim"),
        uncertainty_low=_float_or_none(row.get("Low")),
        uncertainty_high=_float_or_none(row.get("High")),
        applied_filter_rules=rule_text,
        retrieval_metadata_reference=profile.source_path,
        acquisition_catalog_reference=str(catalog_path),
    )


def _dimension_value(row: dict[str, Any], prefix: str) -> str | None:
    for field in ("Dim1", "Dim2", "Dim3"):
        value = row.get(field)
        if isinstance(value, str) and value.startswith(prefix):
            return value
    return None


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _records(
    *,
    values_by_key: dict[tuple[str, int], dict[str, float]],
    provenance_by_key: dict[tuple[str, int], dict[str, WHOValueProvenance]],
    contributing_by_key: dict[tuple[str, int], set[str]],
    findings_by_key: dict[tuple[str, int], list[str]],
    selected_variable_ids: tuple[str, ...],
) -> tuple[WHOHealthRecord, ...]:
    records: list[WHOHealthRecord] = []
    for country_code, year in sorted(values_by_key):
        values = dict(sorted(values_by_key[(country_code, year)].items()))
        provenance = dict(sorted(provenance_by_key[(country_code, year)].items()))
        missingness = {
            variable_id: WHOMissingnessReasonCode.COUNTRY_YEAR_ABSENT
            for variable_id in selected_variable_ids
            if variable_id not in values
        }
        country = normalize_country_identifier(country_code, provider="who")
        records.append(
            WHOHealthRecord(
                canonical_country_code=country_code,
                canonical_country_name=country.canonical_name or country_code,
                year=year,
                values=values,
                value_provenance=provenance,
                contributing_indicator_ids=tuple(sorted(contributing_by_key[(country_code, year)])),
                missingness=missingness,
                findings=tuple(sorted(set(findings_by_key[(country_code, year)]))),
            )
        )
    return tuple(records)


def _quality_summary(
    *,
    mappings: tuple[WHOVariableMapping, ...],
    records: tuple[WHOHealthRecord, ...],
    deferred: tuple[WHODeferredIndicator, ...],
    duplicate_findings: tuple[str, ...],
    unresolved_schema_issues: tuple[str, ...],
    exclusion_counts: Counter[str],
) -> WHOPanelQualitySummary:
    years = sorted({record.year for record in records})
    variable_coverage = {
        mapping.canonical_variable_id: sum(
            1 for record in records if mapping.canonical_variable_id in record.values
        )
        for mapping in mappings
    }
    missingness_by_variable: dict[str, dict[str, int]] = {}
    for mapping in mappings:
        counter: Counter[str] = Counter()
        for record in records:
            reason = record.missingness.get(mapping.canonical_variable_id)
            if reason is not None:
                counter[reason.value] += 1
        missingness_by_variable[mapping.canonical_variable_id] = dict(sorted(counter.items()))
    return WHOPanelQualitySummary(
        selected_indicator_count=len(mappings),
        integrated_indicator_count=len(
            [m for m in mappings if variable_coverage[m.canonical_variable_id] > 0]
        ),
        deferred_indicator_count=len(deferred),
        country_count=len({record.canonical_country_code for record in records}),
        year_range=(years[0], years[-1]) if years else None,
        country_year_record_count=len(records),
        aggregate_exclusions=exclusion_counts[
            WHOMissingnessReasonCode.AGGREGATE_ROW_EXCLUDED.value
        ],
        territory_exclusions=exclusion_counts["territory_exclusions"],
        unknown_entity_exclusions=exclusion_counts["unknown_entity_exclusions"],
        missingness_by_variable=missingness_by_variable,
        variable_coverage=dict(sorted(variable_coverage.items())),
        duplicate_findings=duplicate_findings,
        modeled_series_count=sum(1 for mapping in mappings if mapping.modeled_estimates_accepted),
        projected_rows_excluded=exclusion_counts[
            WHOMissingnessReasonCode.PROJECTED_ROW_EXCLUDED.value
        ],
        sex_specific_rows_excluded=exclusion_counts["sex_specific_rows_excluded"],
        age_specific_rows_excluded=exclusion_counts["age_specific_rows_excluded"],
        unresolved_schema_issues=unresolved_schema_issues,
        analysis_ready=bool(records) and not duplicate_findings and not unresolved_schema_issues,
    )


def _deferred_indicators(
    *,
    catalog: dict[str, Any],
    integrated_indicator_ids: set[str],
) -> tuple[WHODeferredIndicator, ...]:
    deferred: list[WHODeferredIndicator] = []
    for target in catalog.get("targets", []):
        indicator = target.get("selected_who_indicator_id")
        concept = target.get("conceptual_target") or indicator or "unknown WHO target"
        suitability = target.get("integration_suitability")
        if indicator in integrated_indicator_ids:
            continue
        if not target.get("local_snapshot_path"):
            reason = "acquisition deferred; no local provider snapshot exists"
            schema_issue = target.get("failure_details")
            future = "Resolve official WHO GHO endpoint and re-profile before integration."
        elif suitability == WHOSuitability.LOW.value:
            reason = "LOW acquisition suitability; kept out of default panel pending review"
            schema_issue = _schema_issue_from_target(target)
            future = (
                "Create an indicator-specific reviewed filter and validate unique "
                "country-year keys."
            )
        elif indicator is None:
            reason = "catalog target has no resolved WHO indicator ID"
            schema_issue = target.get("failure_details")
            future = "Resolve an official WHO indicator ID and download a snapshot."
        else:
            reason = "not in reviewed Phase 15 default mapping registry"
            schema_issue = _schema_issue_from_target(target)
            future = "Review dimensions, unit, projection status, and duplicate behavior."
        deferred.append(
            WHODeferredIndicator(
                who_indicator_id=indicator,
                conceptual_target=concept,
                suitability_classification=WHOSuitability(suitability) if suitability else None,
                reason_deferred=reason,
                schema_issue=schema_issue,
                required_future_work=future,
                potentially_useful=suitability in {"HIGH", "MEDIUM", "LOW"},
            )
        )
    return tuple(
        sorted(
            deferred,
            key=lambda item: (item.who_indicator_id or "", item.conceptual_target),
        )
    )


def _schema_issue_from_target(target: dict[str, Any]) -> str:
    pieces = []
    if target.get("sex_dimensions"):
        pieces.append(f"sex dimensions {tuple(target['sex_dimensions'])}")
    if target.get("age_dimensions"):
        pieces.append(f"age dimensions {tuple(target['age_dimensions'])}")
    other = target.get("other_important_dimensions") or []
    if other:
        pieces.append(f"other dimensions {tuple(other)}")
    if target.get("warnings"):
        pieces.append(f"warnings {tuple(target['warnings'])}")
    if not target.get("whether_country_year_observations_exist", True):
        pieces.append("no country-year observations")
    return "; ".join(pieces) or "requires indicator-specific schema review"
