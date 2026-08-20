"""Dataset compatibility checks for causal-study definitions."""

from __future__ import annotations

from polaris.causal_studies.models import (
    CausalStudyDefinition,
    CausalStudyFinding,
    ComparisonGroupDiagnostics,
    DatasetCompatibility,
    EntityCoverage,
    FindingCode,
    FindingSeverity,
    PrePostCoverage,
    TreatmentStatus,
)
from polaris.ingestion.models import DatasetIngestionResult
from polaris.registry import DatasetRegistry
from polaris.schemas.dataset import DatasetManifest


def inspect_dataset_compatibility(
    study: CausalStudyDefinition,
    *,
    registry: DatasetRegistry | None = None,
    ingestion_results: tuple[DatasetIngestionResult, ...] = (),
) -> tuple[DatasetCompatibility, ...]:
    manifests = _candidate_manifests(study, registry=registry, ingestion_results=ingestion_results)
    compatibilities = [
        _compatibility_for_manifest(study, manifest, registry=registry) for manifest in manifests
    ]
    return tuple(sorted(compatibilities, key=lambda item: item.dataset_id))


def pre_post_coverage(
    study: CausalStudyDefinition,
    *,
    ingestion_results: tuple[DatasetIngestionResult, ...] = (),
    dataset_id: str | None = None,
) -> PrePostCoverage:
    rows_by_entity = _rows_by_entity(
        study, ingestion_results=ingestion_results, dataset_id=dataset_id
    )
    treated = tuple(
        sorted(
            (
                item
                for item in study.treatment_assignments
                if item.treatment_status is TreatmentStatus.TREATED
            ),
            key=lambda item: item.entity_id,
        )
    )
    controls = control_entities(study, ingestion_results=ingestion_results, dataset_id=dataset_id)
    treated_coverage = tuple(
        _entity_coverage(study, item.entity_id, item.treatment_start, rows_by_entity)
        for item in treated
    )
    control_coverage = tuple(
        _entity_coverage(
            study, entity, study.treatment_timing_rule.analysis_treatment_year, rows_by_entity
        )
        for entity in controls
    )
    findings: list[CausalStudyFinding] = []
    for item in treated_coverage:
        if not item.sufficient_pre:
            findings.append(
                CausalStudyFinding(
                    code=FindingCode.INSUFFICIENT_PRE_PERIODS,
                    severity=FindingSeverity.BLOCKING,
                    message=f"treated entity {item.entity_id} lacks required pre-treatment periods",
                    entity_id=item.entity_id,
                )
            )
        if not item.sufficient_post:
            findings.append(
                CausalStudyFinding(
                    code=FindingCode.INSUFFICIENT_POST_PERIODS,
                    severity=FindingSeverity.BLOCKING,
                    message=(
                        f"treated entity {item.entity_id} lacks required post-treatment periods"
                    ),
                    entity_id=item.entity_id,
                )
            )
    return PrePostCoverage(
        treated_entity_coverage=treated_coverage,
        control_entity_coverage=control_coverage,
        treated_entities_with_sufficient_coverage=tuple(
            item.entity_id
            for item in treated_coverage
            if item.sufficient_pre and item.sufficient_post
        ),
        treated_entities_with_insufficient_coverage=tuple(
            item.entity_id
            for item in treated_coverage
            if not (item.sufficient_pre and item.sufficient_post)
        ),
        control_entities_with_sufficient_coverage=tuple(
            item.entity_id
            for item in control_coverage
            if item.sufficient_pre and item.sufficient_post
        ),
        usable_event_study_window=_usable_event_window(study, treated_coverage),
        findings=tuple(findings),
    )


def comparison_group_diagnostics(
    study: CausalStudyDefinition,
    *,
    ingestion_results: tuple[DatasetIngestionResult, ...] = (),
    dataset_id: str | None = None,
) -> ComparisonGroupDiagnostics:
    treated = {
        item.entity_id
        for item in study.treatment_assignments
        if item.treatment_status is TreatmentStatus.TREATED
    }
    explicit = tuple(sorted(set(study.explicit_comparison_entities) - treated))
    candidates = control_entities(study, ingestion_results=ingestion_results, dataset_id=dataset_id)
    candidates = tuple(entity for entity in candidates if entity not in treated)
    findings = []
    if not explicit and not candidates:
        findings.append(
            CausalStudyFinding(
                code=FindingCode.NO_CONTROL_CANDIDATES,
                severity=FindingSeverity.BLOCKING,
                message="no explicit or never-treated control candidates are available",
            )
        )
    return ComparisonGroupDiagnostics(
        policy=study.comparison_group_policy,
        explicit_control_entities=explicit,
        candidate_never_treated_entities=candidates,
        excluded_entities=tuple(sorted(treated)),
        potential_control_count=len(explicit or candidates),
        findings=tuple(findings),
    )


def control_entities(
    study: CausalStudyDefinition,
    *,
    ingestion_results: tuple[DatasetIngestionResult, ...] = (),
    dataset_id: str | None = None,
) -> tuple[str, ...]:
    explicit = tuple(sorted(set(study.explicit_comparison_entities)))
    if explicit:
        return explicit
    assigned = tuple(
        sorted(
            item.entity_id
            for item in study.treatment_assignments
            if item.treatment_status is TreatmentStatus.NEVER_TREATED
        )
    )
    if assigned:
        return assigned
    rows_by_entity = _rows_by_entity(
        study, ingestion_results=ingestion_results, dataset_id=dataset_id
    )
    treated = {
        item.entity_id
        for item in study.treatment_assignments
        if item.treatment_status is TreatmentStatus.TREATED
    }
    return tuple(sorted(set(rows_by_entity) - treated))


def staggered_treatment_status(study: CausalStudyDefinition) -> str:
    starts = {
        item.treatment_start
        for item in study.treatment_assignments
        if item.treatment_status is TreatmentStatus.TREATED
    }
    return "staggered_unsupported" if len(starts - {None}) > 1 else "common_timing"


def _candidate_manifests(
    study: CausalStudyDefinition,
    *,
    registry: DatasetRegistry | None,
    ingestion_results: tuple[DatasetIngestionResult, ...],
) -> tuple[DatasetManifest, ...]:
    by_id = {
        result.dataset_manifest.dataset_id: result.dataset_manifest for result in ingestion_results
    }
    if registry is not None:
        by_id.update({manifest.dataset_id: manifest for manifest in registry.list_all()})
    if study.candidate_dataset_ids:
        return tuple(
            by_id[dataset_id]
            for dataset_id in sorted(study.candidate_dataset_ids)
            if dataset_id in by_id
        )
    return tuple(by_id[dataset_id] for dataset_id in sorted(by_id))


def _compatibility_for_manifest(
    study: CausalStudyDefinition,
    manifest: DatasetManifest,
    *,
    registry: DatasetRegistry | None,
) -> DatasetCompatibility:
    variable_ids = {item.variable_id for item in manifest.variables}
    entities = set(manifest.geographic_coverage.codes)
    required_entities = {
        item.entity_id
        for item in study.treatment_assignments
        if item.treatment_status in {TreatmentStatus.TREATED, TreatmentStatus.NEVER_TREATED}
    } | set(study.explicit_comparison_entities)
    outcomes = tuple(
        item.variable_id
        for item in study.proposed_outcomes
        if item.dataset_id == manifest.dataset_id
    )
    covariates = tuple(
        item.variable_id
        for item in study.proposed_covariates
        if item.dataset_id == manifest.dataset_id
    )
    findings: list[CausalStudyFinding] = []
    missing_outcomes = tuple(sorted(set(outcomes) - variable_ids))
    missing_covariates = tuple(sorted(set(covariates) - variable_ids))
    if study.entity_variable.variable_id not in variable_ids:
        findings.append(
            CausalStudyFinding(
                code=FindingCode.DATASET_COVERAGE_GAP,
                severity=FindingSeverity.BLOCKING,
                message="entity variable is unavailable in dataset",
                dataset_id=manifest.dataset_id,
                variable_id=study.entity_variable.variable_id,
            )
        )
    if study.time_variable.variable_id not in variable_ids:
        findings.append(
            CausalStudyFinding(
                code=FindingCode.DATASET_COVERAGE_GAP,
                severity=FindingSeverity.BLOCKING,
                message="time variable is unavailable in dataset",
                dataset_id=manifest.dataset_id,
                variable_id=study.time_variable.variable_id,
            )
        )
    for variable_id in missing_outcomes:
        findings.append(
            _variable_finding(FindingCode.OUTCOME_NOT_AVAILABLE, manifest.dataset_id, variable_id)
        )
    for variable_id in missing_covariates:
        findings.append(
            _variable_finding(FindingCode.COVARIATE_NOT_AVAILABLE, manifest.dataset_id, variable_id)
        )
    missing_entities = tuple(sorted(required_entities - entities))
    for entity_id in missing_entities:
        findings.append(
            CausalStudyFinding(
                code=FindingCode.UNRESOLVED_ENTITY,
                severity=FindingSeverity.BLOCKING,
                message=f"entity {entity_id} is not covered by dataset metadata",
                dataset_id=manifest.dataset_id,
                entity_id=entity_id,
            )
        )
    return DatasetCompatibility(
        dataset_id=manifest.dataset_id,
        provider=manifest.provider,
        collection_type=registry.collection_type(manifest.dataset_id)
        if registry and registry.contains(manifest.dataset_id)
        else None,
        entity_variable_available=study.entity_variable.variable_id in variable_ids,
        time_variable_available=study.time_variable.variable_id in variable_ids,
        covered_entities=tuple(sorted(required_entities & entities)),
        missing_entities=missing_entities,
        temporal_start=manifest.temporal_coverage.start,
        temporal_end=manifest.temporal_coverage.end,
        outcome_variables_available=tuple(sorted(set(outcomes) & variable_ids)),
        outcome_variables_missing=missing_outcomes,
        covariates_available=tuple(sorted(set(covariates) & variable_ids)),
        covariates_missing=missing_covariates,
        findings=tuple(findings),
    )


def _variable_finding(code: FindingCode, dataset_id: str, variable_id: str) -> CausalStudyFinding:
    return CausalStudyFinding(
        code=code,
        severity=FindingSeverity.BLOCKING,
        message=f"variable {variable_id} is unavailable in dataset {dataset_id}",
        dataset_id=dataset_id,
        variable_id=variable_id,
    )


def _rows_by_entity(
    study: CausalStudyDefinition,
    *,
    ingestion_results: tuple[DatasetIngestionResult, ...],
    dataset_id: str | None,
) -> dict[str, set[int]]:
    rows: dict[str, set[int]] = {}
    entity_id = study.entity_variable.variable_id
    time_id = study.time_variable.variable_id
    for result in ingestion_results:
        if dataset_id is not None and result.dataset_manifest.dataset_id != dataset_id:
            continue
        for record in result.normalized_records:
            entity = record.values.get(entity_id)
            year = record.values.get(time_id)
            if isinstance(entity, str) and isinstance(year, int):
                rows.setdefault(entity, set()).add(year)
            elif isinstance(entity, str) and isinstance(year, float):
                rows.setdefault(entity, set()).add(int(year))
    return rows


def _entity_coverage(
    study: CausalStudyDefinition,
    entity_id: str,
    treatment_start: int | float | None,
    rows_by_entity: dict[str, set[int]],
) -> EntityCoverage:
    years = rows_by_entity.get(entity_id, set())
    start = int(treatment_start or study.treatment_timing_rule.analysis_treatment_year)
    pre_required = tuple(range(start - study.pre_period_requirements, start))
    post_required = tuple(range(start, start + study.post_period_requirements))
    pre_available = tuple(year for year in pre_required if year in years)
    post_available = tuple(year for year in post_required if year in years)
    return EntityCoverage(
        entity_id=entity_id,
        treatment_start=treatment_start,
        first_available_year=min(years) if years else None,
        last_available_year=max(years) if years else None,
        available_pre_periods=len(pre_available),
        available_post_periods=len(post_available),
        missing_pre_periods=tuple(year for year in pre_required if year not in years),
        missing_post_periods=tuple(year for year in post_required if year not in years),
        sufficient_pre=len(pre_available) >= study.pre_period_requirements,
        sufficient_post=len(post_available) >= study.post_period_requirements,
    )


def _usable_event_window(
    study: CausalStudyDefinition, coverage: tuple[EntityCoverage, ...]
) -> tuple[int, int] | None:
    if study.event_study_window is None or not coverage:
        return None
    min_lead = -min(item.available_pre_periods for item in coverage)
    max_lag = min(item.available_post_periods for item in coverage) - 1
    return (
        max(study.event_study_window.min_event_time, min_lead),
        min(study.event_study_window.max_event_time, max_lag),
    )
