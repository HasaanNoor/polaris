"""Assessment-set validation for deterministic coordination."""

from collections.abc import Sequence

from pydantic import ValidationError

from polaris.agents.models import AGENT_SCHEMA_VERSION, AgentAssessment, AgentDomain
from polaris.coordination.errors import (
    AssessmentSourceMismatchError,
    CoordinationValidationError,
    DuplicateAgentDomainError,
)
from polaris.evidence.models import EVIDENCE_SCHEMA_VERSION


def validate_assessment_set(assessments: Sequence[AgentAssessment]) -> tuple[AgentAssessment, ...]:
    """Validate that assessments can be coordinated without mixing sources."""

    if not assessments:
        raise CoordinationValidationError("coordination requires at least one assessment")

    normalized: list[AgentAssessment] = []
    for assessment in assessments:
        if not isinstance(assessment, AgentAssessment):
            try:
                assessment = AgentAssessment.model_validate(assessment)
            except ValidationError as exc:
                raise CoordinationValidationError(
                    "coordination inputs must be valid AgentAssessment objects"
                ) from exc
        normalized.append(assessment)

    _validate_unique_domains(normalized)
    _validate_unique_assessment_ids(normalized)
    _validate_supported_domains(normalized)
    _validate_same_source(normalized)
    _validate_schema_versions(normalized)
    return tuple(sorted(normalized, key=lambda item: _domain_sort_key(item.agent_domain)))


def _validate_unique_domains(assessments: Sequence[AgentAssessment]) -> None:
    seen: set[AgentDomain] = set()
    duplicates: set[AgentDomain] = set()
    for assessment in assessments:
        if assessment.agent_domain in seen:
            duplicates.add(assessment.agent_domain)
        seen.add(assessment.agent_domain)
    if duplicates:
        values = ", ".join(sorted(domain.value for domain in duplicates))
        raise DuplicateAgentDomainError(f"duplicate assessment domains are not supported: {values}")


def _validate_unique_assessment_ids(assessments: Sequence[AgentAssessment]) -> None:
    ids = [assessment.assessment_id for assessment in assessments]
    if len(ids) != len(set(ids)):
        raise CoordinationValidationError("assessment IDs must be unique")


def _validate_supported_domains(assessments: Sequence[AgentAssessment]) -> None:
    supported = set(AgentDomain)
    unsupported = [
        assessment.agent_domain
        for assessment in assessments
        if assessment.agent_domain not in supported
    ]
    if unsupported:
        values = ", ".join(sorted(str(domain) for domain in unsupported))
        raise CoordinationValidationError(f"unsupported assessment domains: {values}")


def _validate_same_source(assessments: Sequence[AgentAssessment]) -> None:
    first = assessments[0]
    for assessment in assessments[1:]:
        if assessment.source_evidence_artifact_id != first.source_evidence_artifact_id:
            raise AssessmentSourceMismatchError(
                "assessments must reference the same EvidenceArtifact"
            )
        if (
            assessment.provenance.source_evidence_artifact_id
            != first.provenance.source_evidence_artifact_id
        ):
            raise AssessmentSourceMismatchError(
                "assessment provenance must reference the same EvidenceArtifact"
            )
        if assessment.provenance.dataset_id != first.provenance.dataset_id:
            raise AssessmentSourceMismatchError("assessment dataset IDs must match")
        if assessment.provenance.source_checksum_sha256 != first.provenance.source_checksum_sha256:
            raise AssessmentSourceMismatchError("assessment source checksums must match")
        if (
            assessment.provenance.source_analysis_result_id
            != first.provenance.source_analysis_result_id
        ):
            raise AssessmentSourceMismatchError("assessment source analysis result IDs must match")


def _validate_schema_versions(assessments: Sequence[AgentAssessment]) -> None:
    for assessment in assessments:
        if assessment.schema_version != AGENT_SCHEMA_VERSION:
            raise CoordinationValidationError("unsupported Phase 6 assessment schema version")
        if assessment.provenance.phase6_schema_version != AGENT_SCHEMA_VERSION:
            raise CoordinationValidationError("incompatible Phase 6 provenance schema version")
        if assessment.provenance.phase5_schema_version != EVIDENCE_SCHEMA_VERSION:
            raise CoordinationValidationError("incompatible Phase 5 evidence schema version")


def _domain_sort_key(domain: AgentDomain) -> int:
    return tuple(AgentDomain).index(domain)
