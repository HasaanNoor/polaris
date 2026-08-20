"""Design-readiness assessment for Phase 23 causal studies."""

from __future__ import annotations

from typing import Any

from polaris.causal_studies.compatibility import (
    comparison_group_diagnostics,
    inspect_dataset_compatibility,
    pre_post_coverage,
    staggered_treatment_status,
)
from polaris.causal_studies.models import (
    CAUSAL_STUDY_RULESET_VERSION,
    CausalStudyDefinition,
    CausalStudyFinding,
    DesignReadinessAssessment,
    FindingCode,
    FindingSeverity,
    ReadinessStatus,
    ReviewStatus,
    TreatmentStatus,
)
from polaris.causal_studies.provenance import assessment_id_for_payload, registry_provenance
from polaris.causal_studies.validation import validate_study
from polaris.ingestion.models import DatasetIngestionResult
from polaris.registry import DatasetRegistry


def assess_design_readiness(
    study: CausalStudyDefinition,
    *,
    registry: DatasetRegistry | None = None,
    ingestion_results: tuple[DatasetIngestionResult, ...] = (),
    dataset_id: str | None = None,
) -> DesignReadinessAssessment:
    structural = validate_study(study)
    compatibility = inspect_dataset_compatibility(
        study, registry=registry, ingestion_results=ingestion_results
    )
    coverage = pre_post_coverage(study, ingestion_results=ingestion_results, dataset_id=dataset_id)
    controls = comparison_group_diagnostics(
        study, ingestion_results=ingestion_results, dataset_id=dataset_id
    )
    warnings: list[CausalStudyFinding] = []
    blocking = [item for item in structural if item.severity is FindingSeverity.BLOCKING]
    blocking.extend(
        item
        for comp in compatibility
        for item in comp.findings
        if item.severity is FindingSeverity.BLOCKING
    )
    blocking.extend(item for item in coverage.findings if item.severity is FindingSeverity.BLOCKING)
    blocking.extend(item for item in controls.findings if item.severity is FindingSeverity.BLOCKING)
    for variable in study.proposed_covariates:
        if variable.post_treatment_concern:
            warnings.append(
                CausalStudyFinding(
                    code=FindingCode.POST_TREATMENT_COVARIATE_RISK,
                    severity=FindingSeverity.WARNING,
                    message=f"covariate {variable.variable_id} may be post-treatment",
                    dataset_id=variable.dataset_id,
                    variable_id=variable.variable_id,
                )
            )
    warnings.extend(item for item in structural if item.severity is FindingSeverity.WARNING)
    staggered = staggered_treatment_status(study)
    if staggered == "staggered_unsupported":
        finding = CausalStudyFinding(
            code=FindingCode.STAGGERED_TREATMENT_UNSUPPORTED,
            severity=FindingSeverity.BLOCKING,
            message="Phase 22 does not support staggered-treatment causal estimators",
        )
        blocking.append(finding)
    if blocking:
        status = ReadinessStatus.BLOCKED
    elif study.review_status is not ReviewStatus.DESIGN_READY:
        status = ReadinessStatus.NEEDS_REVIEW
    elif warnings:
        status = ReadinessStatus.READY_WITH_WARNINGS
    else:
        status = ReadinessStatus.READY
    payload: dict[str, Any] = {
        "study_id": study.study_id,
        "readiness_status": status.value,
        "structural_findings": [item.model_dump(mode="json") for item in structural],
        "dataset_compatibility": [item.model_dump(mode="json") for item in compatibility],
        "coverage": coverage.model_dump(mode="json"),
        "controls": controls.model_dump(mode="json"),
        "warnings": [item.model_dump(mode="json") for item in warnings],
        "staggered": staggered,
        "ruleset": CAUSAL_STUDY_RULESET_VERSION,
    }
    return DesignReadinessAssessment(
        assessment_id=assessment_id_for_payload(payload),
        study_id=study.study_id,
        readiness_status=status,
        treatment_metadata_status=study.review_status,
        source_status=_source_status(study),
        treated_entity_count=sum(
            1
            for item in study.treatment_assignments
            if item.treatment_status is TreatmentStatus.TREATED
        ),
        potential_control_count=controls.potential_control_count,
        dataset_compatibility=compatibility,
        outcome_coverage=compatibility,
        covariate_coverage=compatibility,
        pre_treatment_coverage=coverage,
        post_treatment_coverage=coverage,
        comparison_group_diagnostics=controls,
        staggered_treatment_status=staggered,
        event_study_feasibility=_event_study_feasibility(study, coverage),
        blocking_findings=tuple(sorted(blocking, key=_finding_key)),
        warnings=tuple(sorted(warnings, key=_finding_key)),
        recommended_human_review_items=_review_items(study, status),
        provenance={
            **registry_provenance(study),
            "ruleset_version": CAUSAL_STUDY_RULESET_VERSION,
        },
    )


def _source_status(study: CausalStudyDefinition) -> ReviewStatus:
    if study.review_status in {
        ReviewStatus.SOURCE_REVIEWED,
        ReviewStatus.METADATA_VALIDATED,
        ReviewStatus.DATA_COMPATIBLE,
        ReviewStatus.DESIGN_READY,
    }:
        return ReviewStatus.SOURCE_REVIEWED
    return study.review_status


def _event_study_feasibility(study: CausalStudyDefinition, coverage) -> str:
    if study.event_study_window is None:
        return "not_requested"
    if coverage.usable_event_study_window is None:
        return "not_feasible"
    if coverage.usable_event_study_window == (
        study.event_study_window.min_event_time,
        study.event_study_window.max_event_time,
    ):
        return "full_window_feasible"
    return "partial_window_feasible"


def _review_items(study: CausalStudyDefinition, status: ReadinessStatus) -> tuple[str, ...]:
    items = [
        (
            "Design-ready means metadata/data structure is sufficient, "
            "not that identifying assumptions are true."
        )
    ]
    if status is not ReadinessStatus.READY:
        items.append("Human source and design review is required before Phase 22 estimation.")
    if study.comparison_group_policy.value == "never_treated_within_scope":
        items.append("Candidate controls require human selection before conversion.")
    return tuple(items)


def _finding_key(item: CausalStudyFinding) -> tuple[str, str, str, str]:
    return (
        item.severity.value,
        item.code.value,
        item.entity_id or "",
        item.variable_id or "",
    )
