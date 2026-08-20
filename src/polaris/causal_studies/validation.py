"""Structural validation for reviewed causal-study definitions."""

from __future__ import annotations

from collections import Counter

from polaris.analysis.causal.models import CausalMethod
from polaris.causal_studies.models import (
    CausalStudyDefinition,
    CausalStudyFinding,
    FindingCode,
    FindingSeverity,
    ReviewStatus,
    TreatmentStatus,
)


def validate_study(study: CausalStudyDefinition) -> tuple[CausalStudyFinding, ...]:
    findings: list[CausalStudyFinding] = []
    declared_source_ids = {source.source_id for source in study.sources}
    source_ids = set(study.source_ids) | set(study.intervention.source_ids) | declared_source_ids
    if not source_ids:
        findings.append(_blocking(FindingCode.MISSING_TREATMENT_SOURCE, "study has no source IDs"))
    missing_declared = (
        set(study.source_ids) | set(study.intervention.source_ids)
    ) - declared_source_ids
    source_counts = Counter(source.source_id for source in study.sources)
    for source_id, count in sorted(source_counts.items()):
        if count > 1:
            findings.append(
                _blocking(
                    FindingCode.MISSING_SOURCE_REFERENCE,
                    f"duplicate TreatmentSource record for {source_id}",
                    source_id=source_id,
                )
            )
    for source_id in sorted(missing_declared):
        findings.append(
            _blocking(
                FindingCode.MISSING_SOURCE_REFERENCE,
                f"source ID {source_id} lacks a TreatmentSource record",
                source_id=source_id,
            )
        )
    findings.extend(_source_reference_findings(study, source_ids))
    findings.extend(_assignment_findings(study))
    findings.extend(_timing_findings(study))
    if not set(study.supported_methods) <= {
        CausalMethod.DIFFERENCE_IN_DIFFERENCES,
        CausalMethod.EVENT_STUDY,
    }:
        findings.append(
            _blocking(
                FindingCode.METHOD_NOT_SUPPORTED,
                "study references a causal method unsupported by Phase 22",
            )
        )
    if study.review_status in {ReviewStatus.DRAFT, ReviewStatus.SOURCE_REVIEWED}:
        findings.append(
            CausalStudyFinding(
                code=FindingCode.SOURCE_REVIEW_REQUIRED,
                severity=FindingSeverity.WARNING,
                message="study requires human review before design readiness",
            )
        )
    return tuple(
        sorted(findings, key=lambda item: (item.severity.value, item.code.value, item.message))
    )


def _source_reference_findings(
    study: CausalStudyDefinition, source_ids: set[str]
) -> tuple[CausalStudyFinding, ...]:
    findings: list[CausalStudyFinding] = []
    for source_id in study.treatment_timing_rule.source_ids:
        if source_id not in source_ids:
            findings.append(
                _blocking(
                    FindingCode.MISSING_SOURCE_REFERENCE,
                    f"treatment timing source {source_id} is not declared",
                    source_id=source_id,
                )
            )
    for assignment in study.treatment_assignments:
        if (
            assignment.treatment_status is not TreatmentStatus.UNKNOWN
            and not assignment.assignment_source_ids
        ):
            findings.append(
                _blocking(
                    FindingCode.MISSING_TREATMENT_SOURCE,
                    f"assignment for {assignment.entity_id} has no source IDs",
                    entity_id=assignment.entity_id,
                )
            )
        for source_id in assignment.assignment_source_ids:
            if source_id not in source_ids:
                findings.append(
                    _blocking(
                        FindingCode.MISSING_SOURCE_REFERENCE,
                        f"assignment source {source_id} is not declared",
                        entity_id=assignment.entity_id,
                        source_id=source_id,
                    )
                )
    return tuple(findings)


def _assignment_findings(study: CausalStudyDefinition) -> tuple[CausalStudyFinding, ...]:
    findings: list[CausalStudyFinding] = []
    counts = Counter(assignment.entity_id for assignment in study.treatment_assignments)
    for entity_id, count in sorted(counts.items()):
        if count > 1:
            records = [item for item in study.treatment_assignments if item.entity_id == entity_id]
            statuses = {item.treatment_status for item in records}
            starts = {item.treatment_start for item in records}
            code = (
                FindingCode.CONTRADICTORY_ASSIGNMENT
                if len(statuses) > 1 or len(starts) > 1
                else FindingCode.DUPLICATE_ASSIGNMENT
            )
            findings.append(
                _blocking(
                    code,
                    f"entity {entity_id} has duplicate assignment records",
                    entity_id=entity_id,
                )
            )
    treated = [
        item
        for item in study.treatment_assignments
        if item.treatment_status is TreatmentStatus.TREATED
    ]
    if not treated:
        findings.append(_blocking(FindingCode.UNRESOLVED_ENTITY, "study has no treated entities"))
    return tuple(findings)


def _timing_findings(study: CausalStudyDefinition) -> tuple[CausalStudyFinding, ...]:
    findings: list[CausalStudyFinding] = []
    role = study.treatment_timing_rule.date_role.value
    if getattr(study.intervention, role) is None:
        findings.append(
            _blocking(
                FindingCode.MISSING_TREATMENT_DATE,
                f"intervention lacks {role} required by treatment timing rule",
            )
        )
    starts = {
        assignment.treatment_start
        for assignment in study.treatment_assignments
        if assignment.treatment_status is TreatmentStatus.TREATED
    }
    if None in starts:
        findings.append(
            _blocking(FindingCode.MISSING_TREATMENT_DATE, "treated assignment lacks start")
        )
    if len(starts - {None}) > 1:
        findings.append(
            _blocking(
                FindingCode.STAGGERED_TREATMENT_UNSUPPORTED,
                (
                    "treated entities have differing treatment starts; "
                    "Phase 22 rejects staggered adoption"
                ),
            )
        )
    if (
        study.treatment_timing_rule.analysis_treatment_year not in starts
        and len(starts - {None}) == 1
    ):
        findings.append(
            CausalStudyFinding(
                code=FindingCode.AMBIGUOUS_TREATMENT_TIMING,
                severity=FindingSeverity.WARNING,
                message=(
                    "analysis treatment year differs from assignment start; mapping requires review"
                ),
            )
        )
    return tuple(findings)


def _blocking(
    code: FindingCode,
    message: str,
    *,
    entity_id: str | None = None,
    source_id: str | None = None,
) -> CausalStudyFinding:
    return CausalStudyFinding(
        code=code,
        severity=FindingSeverity.BLOCKING,
        message=message,
        entity_id=entity_id,
        source_id=source_id,
    )
