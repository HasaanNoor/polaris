"""Public synchronous API for deterministic country-year harmonization."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime
from typing import NamedTuple

from polaris import __version__
from polaris.harmonization.compatibility import validate_variable_compatibility
from polaris.harmonization.countries import normalize_country_identifier
from polaris.harmonization.errors import (
    HarmonizationCompatibilityError,
    HarmonizationRequestError,
)
from polaris.harmonization.models import (
    DatasetHarmonizationProvenance,
    DuplicateKeyBehavior,
    GeographicEntityType,
    HarmonizationFinding,
    HarmonizationFindingCode,
    HarmonizationQualitySummary,
    HarmonizationRequest,
    HarmonizationSeverity,
    HarmonizedDataset,
    HarmonizedRecord,
    JoinType,
    MissingnessReasonCode,
    TransformationRule,
    ValueProvenance,
    VariableCatalogEntry,
    VariableMapping,
)
from polaris.harmonization.provenance import deterministic_harmonized_dataset_id
from polaris.harmonization.temporal import normalize_year
from polaris.ingestion.models import DatasetIngestionResult, NormalizedRecord, NormalizedValue


class _SelectedValue(NamedTuple):
    key: tuple[str, int]
    country_name: str
    value: NormalizedValue
    provenance: ValueProvenance
    dataset_id: str
    provider: str
    canonical_variable_id: str
    source_row_reference: str


class _DatasetSelection(NamedTuple):
    dataset_id: str
    keys: set[tuple[str, int]]
    values: dict[tuple[str, int, str], list[_SelectedValue]]
    findings: tuple[HarmonizationFinding, ...]


def harmonize_datasets(*, request: HarmonizationRequest) -> HarmonizedDataset:
    """Build one immutable country-year dataset from explicit validated inputs."""

    _validate_dataset_fields(request)
    compatibility_findings = validate_variable_compatibility(request)
    fatal = tuple(
        finding
        for finding in compatibility_findings
        if finding.severity is HarmonizationSeverity.FATAL
    )
    if fatal:
        raise HarmonizationCompatibilityError(fatal[0].message)

    selections = _select_values(request)
    duplicate_findings = tuple(
        finding
        for selection in selections
        for finding in selection.findings
        if finding.code is HarmonizationFindingCode.DUPLICATE_COUNTRY_YEAR
    )
    if (
        duplicate_findings
        and request.strictness.duplicate_key_behavior is DuplicateKeyBehavior.REJECT
    ):
        raise HarmonizationCompatibilityError(duplicate_findings[0].message)

    join_keys = _join_keys(request, selections)
    records, record_findings = _build_records(request, selections, join_keys)
    findings = tuple(
        sorted(
            (
                *compatibility_findings,
                *(f for s in selections for f in s.findings),
                *record_findings,
            ),
            key=_finding_sort_key,
        )
    )
    value_provenance = tuple(
        provenance
        for record in records
        for _, provenance in sorted(record.value_provenance.items())
    )
    source_checksums = {
        result.dataset_manifest.dataset_id: result.checksum_sha256
        for result in request.ingestion_results
    }
    dataset_id = deterministic_harmonized_dataset_id(request)
    quality_summary = _quality_summary(request, records, findings, selections)
    return HarmonizedDataset(
        harmonized_dataset_id=dataset_id,
        request=request,
        input_dataset_references=tuple(sorted(source_checksums)),
        canonical_variable_catalog=_variable_catalog(request),
        records=records,
        quality_summary=quality_summary,
        findings=findings,
        value_level_provenance=value_provenance,
        dataset_level_provenance=DatasetHarmonizationProvenance(
            input_dataset_ids=tuple(sorted(source_checksums)),
            source_checksums=source_checksums,
            join_type=request.join_type,
            anchor_dataset_id=request.anchor_dataset_id,
            ruleset_version=request.ruleset_version,
        ),
        source_checksums=source_checksums,
        software_version=f"polaris-{__version__}",
        ruleset_version=request.ruleset_version,
    )


def _validate_dataset_fields(request: HarmonizationRequest) -> None:
    manifests = {result.dataset_manifest.dataset_id: result for result in request.ingestion_results}
    for config in request.dataset_configs:
        result = manifests[config.dataset_id]
        variables = {variable.variable_id for variable in result.dataset_manifest.variables}
        variables.update(
            variable.source_field_name or variable.variable_id
            for variable in result.dataset_manifest.variables
        )
        required = [config.country_field, config.year_field]
        if config.country_name_field is not None:
            required.append(config.country_name_field)
        if config.geographic_level_field is not None:
            required.append(config.geographic_level_field)
        missing = [field for field in required if field not in variables]
        if missing:
            raise HarmonizationRequestError(
                f"{config.dataset_id} missing harmonization field(s): {', '.join(missing)}"
            )


def _select_values(request: HarmonizationRequest) -> tuple[_DatasetSelection, ...]:
    results = {result.dataset_manifest.dataset_id: result for result in request.ingestion_results}
    configs = {config.dataset_id: config for config in request.dataset_configs}
    mappings_by_dataset: dict[str, list[VariableMapping]] = defaultdict(list)
    for mapping in request.variable_mappings:
        mappings_by_dataset[mapping.source_dataset_id].append(mapping)

    selections: list[_DatasetSelection] = []
    for dataset_id in sorted(results):
        result = results[dataset_id]
        config = configs[dataset_id]
        values: dict[tuple[str, int, str], list[_SelectedValue]] = defaultdict(list)
        keys: set[tuple[str, int]] = set()
        findings: list[HarmonizationFinding] = []
        for record in result.normalized_records:
            country = normalize_country_identifier(
                _record_value(record, config.country_field),
                provider=config.provider,
                source_name=(
                    _record_value(record, config.country_name_field)
                    if config.country_name_field is not None
                    else None
                ),
            )
            if country.entity_type is GeographicEntityType.UNKNOWN:
                findings.append(
                    _finding(
                        HarmonizationSeverity.WARNING,
                        HarmonizationFindingCode.UNMAPPED_COUNTRY,
                        f"unmapped geographic entity {country.source_value}",
                        result,
                        config.provider,
                        record,
                        raw_value=country.source_value,
                    )
                )
                continue
            if (
                request.strictness.exclude_aggregate_entities
                and country.entity_type
                in {
                    GeographicEntityType.REGION,
                    GeographicEntityType.INCOME_GROUP,
                    GeographicEntityType.GLOBAL_AGGREGATE,
                }
                and not config.include_aggregate_entities
            ):
                findings.append(
                    _finding(
                        HarmonizationSeverity.INFO,
                        HarmonizationFindingCode.AGGREGATE_ENTITY_EXCLUDED,
                        f"aggregate entity excluded: {country.source_value}",
                        result,
                        config.provider,
                        record,
                        raw_value=country.source_value,
                    )
                )
                continue
            if (
                request.strictness.exclude_territories
                and country.entity_type is GeographicEntityType.TERRITORY
            ):
                findings.append(
                    _finding(
                        HarmonizationSeverity.INFO,
                        HarmonizationFindingCode.TERRITORY_EXCLUDED,
                        f"territory excluded: {country.source_value}",
                        result,
                        config.provider,
                        record,
                        raw_value=country.source_value,
                    )
                )
                continue
            year = normalize_year(_record_value(record, config.year_field))
            if year is None:
                findings.append(
                    _finding(
                        HarmonizationSeverity.WARNING,
                        HarmonizationFindingCode.INVALID_YEAR,
                        "record does not contain an annual calendar year",
                        result,
                        config.provider,
                        record,
                        raw_value=str(_record_value(record, config.year_field)),
                    )
                )
                continue
            if request.temporal_scope is not None:
                if request.temporal_scope.start is not None and year < request.temporal_scope.start:
                    continue
                if request.temporal_scope.end is not None and year > request.temporal_scope.end:
                    continue
            key = (country.canonical_code or country.source_value, year)
            keys.add(key)
            for mapping in mappings_by_dataset.get(dataset_id, []):
                if not _matches_filters(record, mapping.row_filters):
                    continue
                value = _record_value(record, mapping.source_field_name)
                if value is None:
                    findings.append(
                        HarmonizationFinding(
                            severity=HarmonizationSeverity.INFO,
                            code=HarmonizationFindingCode.SOURCE_VALUE_MISSING,
                            message=f"source value missing for {mapping.canonical_variable_id}",
                            dataset_id=dataset_id,
                            provider=config.provider,
                            canonical_variable_id=mapping.canonical_variable_id,
                            canonical_country_code=key[0],
                            year=year,
                            source_row_number=record.row_number,
                        )
                    )
                    continue
                transformed = _transform_value(value, mapping)
                provenance = _value_provenance(
                    result=result,
                    record=record,
                    mapping=mapping,
                    config_provider=config.provider,
                    country_identifier=_record_value(record, config.country_field),
                    year_value=_record_value(record, config.year_field),
                    value=value,
                    transformed=transformed,
                )
                values[(key[0], year, mapping.canonical_variable_id)].append(
                    _SelectedValue(
                        key=key,
                        country_name=country.canonical_name or key[0],
                        value=transformed,
                        provenance=provenance,
                        dataset_id=dataset_id,
                        provider=config.provider,
                        canonical_variable_id=mapping.canonical_variable_id,
                        source_row_reference=f"{dataset_id}:{record.row_number}",
                    )
                )
                if mapping.transformation_rule not in {
                    TransformationRule.NONE,
                    TransformationRule.RENAME_ONLY,
                }:
                    findings.append(
                        HarmonizationFinding(
                            severity=HarmonizationSeverity.INFO,
                            code=HarmonizationFindingCode.TRANSFORMATION_APPLIED,
                            message=f"transformation applied: {mapping.transformation_rule.value}",
                            dataset_id=dataset_id,
                            provider=config.provider,
                            canonical_variable_id=mapping.canonical_variable_id,
                            canonical_country_code=key[0],
                            year=year,
                            source_row_number=record.row_number,
                        )
                    )
        findings.extend(_duplicate_findings(result, config.provider, values))
        selections.append(
            _DatasetSelection(
                dataset_id=dataset_id,
                keys=keys,
                values=dict(values),
                findings=tuple(findings),
            )
        )
    return tuple(selections)


def _join_keys(
    request: HarmonizationRequest,
    selections: tuple[_DatasetSelection, ...],
) -> tuple[tuple[str, int], ...]:
    key_sets = {selection.dataset_id: selection.keys for selection in selections}
    if request.join_type is JoinType.INNER:
        keys = set.intersection(*(set(selection.keys) for selection in selections))
    elif request.join_type is JoinType.LEFT:
        if request.anchor_dataset_id is None:
            raise HarmonizationRequestError("left join requires anchor_dataset_id")
        keys = set(key_sets[request.anchor_dataset_id])
    else:
        keys = set.union(*(set(selection.keys) for selection in selections))
    return tuple(sorted(keys, key=lambda item: (item[0], item[1])))


def _build_records(
    request: HarmonizationRequest,
    selections: tuple[_DatasetSelection, ...],
    join_keys: tuple[tuple[str, int], ...],
) -> tuple[tuple[HarmonizedRecord, ...], tuple[HarmonizationFinding, ...]]:
    values_by_key: dict[tuple[str, int, str], list[_SelectedValue]] = defaultdict(list)
    dataset_keys = {selection.dataset_id: selection.keys for selection in selections}
    for selection in selections:
        for key, values in selection.values.items():
            values_by_key[key].extend(values)
    variables = tuple(mapping.canonical_variable_id for mapping in request.variable_mappings)
    precedence = {
        rule.canonical_variable_id: rule.provider_order for rule in request.provider_precedence
    }
    records: list[HarmonizedRecord] = []
    findings: list[HarmonizationFinding] = []
    for country_code, year in join_keys:
        record_values: dict[str, NormalizedValue] = {}
        provenance: dict[str, ValueProvenance] = {}
        missingness: dict[str, MissingnessReasonCode] = {}
        source_refs: set[str] = set()
        contributing: set[str] = set()
        country_name = country_code
        record_findings: list[HarmonizationFinding] = []
        for variable_id in variables:
            candidates = values_by_key.get((country_code, year, variable_id), [])
            if not candidates:
                missingness[variable_id] = MissingnessReasonCode.JOIN_INDUCED_MISSING
                record_findings.append(
                    HarmonizationFinding(
                        severity=HarmonizationSeverity.INFO,
                        code=HarmonizationFindingCode.JOIN_MISSING_VALUE,
                        message=f"missing joined value for {variable_id}",
                        canonical_variable_id=variable_id,
                        canonical_country_code=country_code,
                        year=year,
                    )
                )
                continue
            selected, conflict_findings = _select_candidate(
                candidates,
                variable_id,
                country_code,
                year,
                precedence.get(variable_id),
            )
            record_findings.extend(conflict_findings)
            if selected is None:
                missingness[variable_id] = MissingnessReasonCode.UNRESOLVED_DUPLICATE
                continue
            record_values[variable_id] = selected.value
            provenance[variable_id] = selected.provenance
            source_refs.add(selected.source_row_reference)
            contributing.add(selected.dataset_id)
            country_name = selected.country_name
        for dataset_id, keys in dataset_keys.items():
            if (country_code, year) not in keys:
                record_findings.append(
                    HarmonizationFinding(
                        severity=HarmonizationSeverity.INFO,
                        code=HarmonizationFindingCode.JOIN_MISSING_VALUE,
                        message=f"country-year absent from {dataset_id}",
                        dataset_id=dataset_id,
                        canonical_country_code=country_code,
                        year=year,
                    )
                )
        findings.extend(record_findings)
        records.append(
            HarmonizedRecord(
                canonical_country_code=country_code,
                canonical_country_name=country_name,
                year=year,
                values=dict(sorted(record_values.items())),
                value_provenance=dict(sorted(provenance.items())),
                contributing_dataset_ids=tuple(sorted(contributing)),
                source_row_references=tuple(sorted(source_refs)),
                missingness=dict(sorted(missingness.items())),
                findings=tuple(sorted(record_findings, key=_finding_sort_key)),
            )
        )
    return tuple(records), tuple(findings)


def _select_candidate(
    candidates: list[_SelectedValue],
    variable_id: str,
    country_code: str,
    year: int,
    provider_order: tuple[str, ...] | None,
) -> tuple[_SelectedValue | None, tuple[HarmonizationFinding, ...]]:
    unique_values = {repr(candidate.value) for candidate in candidates}
    if len(candidates) == 1:
        return candidates[0], ()
    findings: list[HarmonizationFinding] = [
        HarmonizationFinding(
            severity=HarmonizationSeverity.WARNING,
            code=HarmonizationFindingCode.CONFLICTING_SOURCE_VALUES,
            message=f"multiple source values found for {variable_id}",
            canonical_variable_id=variable_id,
            canonical_country_code=country_code,
            year=year,
        )
    ]
    if provider_order is None:
        if len(unique_values) == 1:
            selected = sorted(candidates, key=lambda item: item.source_row_reference)[0]
            return selected, tuple(findings)
        return None, tuple(findings)
    for provider in provider_order:
        provider_candidates = [
            candidate for candidate in candidates if candidate.provider == provider
        ]
        if provider_candidates:
            findings.append(
                HarmonizationFinding(
                    severity=HarmonizationSeverity.INFO,
                    code=HarmonizationFindingCode.PROVIDER_PRECEDENCE_APPLIED,
                    message=f"provider precedence selected {provider} for {variable_id}",
                    provider=provider,
                    canonical_variable_id=variable_id,
                    canonical_country_code=country_code,
                    year=year,
                )
            )
            selected = sorted(provider_candidates, key=lambda item: item.source_row_reference)[0]
            return selected, tuple(findings)
    return None, tuple(findings)


def _duplicate_findings(
    result: DatasetIngestionResult,
    provider: str,
    values: dict[tuple[str, int, str], list[_SelectedValue]],
) -> tuple[HarmonizationFinding, ...]:
    findings: list[HarmonizationFinding] = []
    for country_code, year, variable_id in sorted(values):
        if len(values[(country_code, year, variable_id)]) > 1:
            findings.append(
                HarmonizationFinding(
                    severity=HarmonizationSeverity.WARNING,
                    code=HarmonizationFindingCode.DUPLICATE_COUNTRY_YEAR,
                    message=f"duplicate country-year value for {variable_id}",
                    dataset_id=result.dataset_manifest.dataset_id,
                    provider=provider,
                    canonical_variable_id=variable_id,
                    canonical_country_code=country_code,
                    year=year,
                )
            )
    return tuple(findings)


def _record_value(record: NormalizedRecord, field: str | None) -> NormalizedValue:
    if field is None:
        return None
    if field in record.values:
        return record.values[field]
    for variable_id, source_column in record.source_columns.items():
        if source_column == field:
            return record.values.get(variable_id)
    return record.source_columns.get(field)


def _matches_filters(record: NormalizedRecord, filters: dict[str, str]) -> bool:
    for field, expected in filters.items():
        value = _record_value(record, field)
        if "" if value is None else str(value) != expected:
            return False
    return True


def _transform_value(value: NormalizedValue, mapping: VariableMapping) -> NormalizedValue:
    if value is None:
        return None
    if mapping.transformation_rule is TransformationRule.PERCENT_TO_PROPORTION:
        return float(value) / 100.0
    if mapping.transformation_rule is TransformationRule.PROPORTION_TO_PERCENT:
        return float(value) * 100.0
    return value


def _value_provenance(
    *,
    result: DatasetIngestionResult,
    record: NormalizedRecord,
    mapping: VariableMapping,
    config_provider: str,
    country_identifier: NormalizedValue,
    year_value: NormalizedValue,
    value: NormalizedValue,
    transformed: NormalizedValue,
) -> ValueProvenance:
    return ValueProvenance(
        canonical_variable_id=mapping.canonical_variable_id,
        source_dataset_id=result.dataset_manifest.dataset_id,
        source_provider=config_provider,
        source_checksum=result.checksum_sha256,
        source_variable_id=mapping.source_variable_id,
        source_field_name=mapping.source_field_name,
        source_row_number=record.row_number,
        source_line_number=record.source_line_number,
        original_geographic_identifier=str(country_identifier),
        original_year_value=str(year_value),
        original_raw_value=_json_scalar(value),
        normalized_value=transformed,
        transformation_applied=mapping.transformation_rule,
        unit=mapping.canonical_unit,
        retrieval_timestamp=result.dataset_manifest.retrieval_timestamp,
        manifest_id=result.dataset_manifest.dataset_id,
        source_path=result.source_metadata.source_path,
    )


def _json_scalar(value: NormalizedValue) -> str | int | float | bool | None:
    if isinstance(value, date | datetime):
        return value.isoformat()
    return value


def _finding(
    severity: HarmonizationSeverity,
    code: HarmonizationFindingCode,
    message: str,
    result: DatasetIngestionResult,
    provider: str,
    record: NormalizedRecord,
    *,
    raw_value: str | None = None,
) -> HarmonizationFinding:
    return HarmonizationFinding(
        severity=severity,
        code=code,
        message=message,
        dataset_id=result.dataset_manifest.dataset_id,
        provider=provider,
        source_row_number=record.row_number,
        raw_value=raw_value,
    )


def _variable_catalog(request: HarmonizationRequest) -> tuple[VariableCatalogEntry, ...]:
    return tuple(
        VariableCatalogEntry(
            canonical_variable_id=mapping.canonical_variable_id,
            canonical_label=mapping.canonical_label,
            provider=mapping.source_provider,
            source_dataset_id=mapping.source_dataset_id,
            source_variable_id=mapping.source_variable_id,
            source_field_name=mapping.source_field_name,
            unit=mapping.canonical_unit,
            conceptual_definition=mapping.conceptual_definition,
            transformation_rule=mapping.transformation_rule,
        )
        for mapping in sorted(
            request.variable_mappings,
            key=lambda item: (item.canonical_variable_id, item.source_dataset_id),
        )
    )


def _quality_summary(
    request: HarmonizationRequest,
    records: tuple[HarmonizedRecord, ...],
    findings: tuple[HarmonizationFinding, ...],
    selections: tuple[_DatasetSelection, ...],
) -> HarmonizationQualitySummary:
    missing_by_variable: dict[str, Counter[str]] = defaultdict(Counter)
    missing_by_source: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        for variable_id, reason in record.missingness.items():
            missing_by_variable[variable_id][reason.value] += 1
    for finding in findings:
        if (
            finding.dataset_id is not None
            and finding.code is HarmonizationFindingCode.JOIN_MISSING_VALUE
        ):
            missing_by_source[finding.dataset_id][
                MissingnessReasonCode.COUNTRY_YEAR_ABSENT.value
            ] += 1
        if (
            finding.dataset_id is not None
            and finding.code is HarmonizationFindingCode.SOURCE_VALUE_MISSING
        ):
            missing_by_source[finding.dataset_id][
                MissingnessReasonCode.SOURCE_VALUE_MISSING.value
            ] += 1
    conflicts = Counter(
        finding.canonical_variable_id or "_dataset"
        for finding in findings
        if finding.code is HarmonizationFindingCode.CONFLICTING_SOURCE_VALUES
    )
    transforms = Counter(
        finding.canonical_variable_id or "_dataset"
        for finding in findings
        if finding.code is HarmonizationFindingCode.TRANSFORMATION_APPLIED
    )
    unresolved = tuple(
        sorted(
            {
                finding.code.value
                for finding in findings
                if finding.severity in {HarmonizationSeverity.FATAL, HarmonizationSeverity.WARNING}
            }
        )
    )
    variables = tuple(sorted({variable for record in records for variable in record.values}))
    return HarmonizationQualitySummary(
        input_dataset_count=len(request.ingestion_results),
        input_accepted_record_counts={
            result.dataset_manifest.dataset_id: result.validation_report.accepted_row_count
            for result in request.ingestion_results
        },
        output_country_year_record_count=len(records),
        countries_represented=tuple(sorted({record.canonical_country_code for record in records})),
        years_represented=tuple(sorted({record.year for record in records})),
        variables_represented=variables,
        matched_country_count=len({record.canonical_country_code for record in records}),
        unmapped_geographic_entities=dict(
            Counter(
                finding.raw_value or "unknown"
                for finding in findings
                if finding.code is HarmonizationFindingCode.UNMAPPED_COUNTRY
            )
        ),
        aggregate_entities_excluded=sum(
            1
            for finding in findings
            if finding.code is HarmonizationFindingCode.AGGREGATE_ENTITY_EXCLUDED
        ),
        invalid_temporal_records=sum(
            1 for finding in findings if finding.code is HarmonizationFindingCode.INVALID_YEAR
        ),
        duplicate_keys=sum(
            1
            for finding in findings
            if finding.code is HarmonizationFindingCode.DUPLICATE_COUNTRY_YEAR
        ),
        conflict_counts=dict(conflicts),
        missingness_by_variable={key: dict(value) for key, value in missing_by_variable.items()},
        missingness_by_source={key: dict(value) for key, value in missing_by_source.items()},
        join_coverage={selection.dataset_id: len(selection.keys) for selection in selections},
        transformations_applied=dict(transforms),
        unresolved_issues=unresolved,
        analysis_ready=bool(records)
        and not any(finding.severity is HarmonizationSeverity.FATAL for finding in findings),
    )


def _finding_sort_key(finding: HarmonizationFinding) -> tuple[str, str, int, str, str]:
    return (
        finding.dataset_id or "",
        finding.canonical_country_code or "",
        finding.year or -1,
        finding.canonical_variable_id or "",
        finding.code.value,
    )
