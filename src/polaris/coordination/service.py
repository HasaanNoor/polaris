"""Public service API for deterministic Phase 7 coordination."""

from datetime import UTC, datetime

from pydantic import ValidationError

from polaris import __version__
from polaris.agents.models import AgentAssessment, AgentDomain, UnsupportedInferenceCode
from polaris.coordination.agreement import identify_agreements, identify_divergences
from polaris.coordination.coverage import aggregate_domain_coverage
from polaris.coordination.errors import CoordinationValidationError
from polaris.coordination.gaps import identify_domain_gaps, identify_evidence_gaps
from polaris.coordination.models import (
    COORDINATION_RULESET_VERSION,
    COORDINATION_SCHEMA_VERSION,
    DOMAIN_ORDER,
    CoordinatedAssessment,
    CoordinationFinding,
    CoordinationFindingCode,
    CoordinationProvenance,
    CoordinationRequest,
)
from polaris.coordination.overlap import (
    claim_domain_map,
    evidence_domain_map,
    shared_limitations,
    unsupported_inference_aggregation,
)
from polaris.coordination.validation import validate_assessment_set
from polaris.evidence.provenance import deterministic_id
from polaris.schemas.common import WarningSeverity


def coordinate_assessments(
    *,
    assessments: tuple[AgentAssessment, ...] | None = None,
    request: CoordinationRequest | None = None,
    coordination_timestamp: datetime | None = None,
) -> CoordinatedAssessment:
    """Coordinate Phase 6 domain assessments into one deterministic structural result."""

    if request is None:
        try:
            request = CoordinationRequest(assessments=assessments or ())
        except ValidationError as exc:
            raise CoordinationValidationError(
                "coordination inputs must be valid AgentAssessment objects"
            ) from exc
    validated = validate_assessment_set(request.assessments)

    first = validated[0]
    participating_domains = tuple(assessment.agent_domain for assessment in validated)
    missing_domains = tuple(
        domain for domain in DOMAIN_ORDER if domain not in participating_domains
    )
    source_assessment_ids = tuple(assessment.assessment_id for assessment in validated)
    coverage = aggregate_domain_coverage(validated)
    evidence_map = evidence_domain_map(validated)
    claim_map = claim_domain_map(validated)
    limitations = shared_limitations(validated)
    unsupported = unsupported_inference_aggregation(validated)
    agreements = identify_agreements(validated, evidence_map=evidence_map, claim_map=claim_map)
    divergences = identify_divergences(validated, evidence_map=evidence_map, claim_map=claim_map)
    domain_gaps = identify_domain_gaps(coverage)
    evidence_gaps = identify_evidence_gaps(evidence_map=evidence_map, claim_map=claim_map)
    findings = _coordination_findings(
        assessments=validated,
        missing_domains=missing_domains,
        evidence_map=evidence_map,
        shared_limitations=limitations,
        unsupported_inferences=unsupported,
    )
    provenance = CoordinationProvenance(
        source_evidence_artifact_id=first.source_evidence_artifact_id,
        source_assessment_ids=source_assessment_ids,
        source_analysis_result_id=first.provenance.source_analysis_result_id,
        dataset_id=first.provenance.dataset_id,
        source_checksum_sha256=first.provenance.source_checksum_sha256,
        participating_domains=participating_domains,
        missing_domains=missing_domains,
        coordination_timestamp=coordination_timestamp or datetime.now(UTC),
        software_version=f"polaris-{__version__}",
        phase5_schema_version=first.provenance.phase5_schema_version,
        phase6_schema_version=first.provenance.phase6_schema_version,
    )
    coordinated_id = _coordinated_assessment_id(
        source_evidence_artifact_id=first.source_evidence_artifact_id,
        source_assessment_ids=source_assessment_ids,
        participating_domains=participating_domains,
    )
    return CoordinatedAssessment(
        coordinated_assessment_id=coordinated_id,
        source_evidence_artifact_id=first.source_evidence_artifact_id,
        source_analysis_result_id=first.provenance.source_analysis_result_id,
        dataset_id=first.provenance.dataset_id,
        source_checksum_sha256=first.provenance.source_checksum_sha256,
        participating_domains=participating_domains,
        missing_domains=missing_domains,
        source_assessment_ids=source_assessment_ids,
        domain_coverage=coverage,
        evidence_domain_map=evidence_map,
        claim_domain_map=claim_map,
        agreements=agreements,
        divergences=divergences,
        shared_limitations=limitations,
        shared_unsupported_inferences=unsupported,
        evidence_gaps=evidence_gaps,
        domain_gaps=domain_gaps,
        coordination_findings=findings,
        provenance=provenance,
    )


def _coordination_findings(
    *,
    assessments: tuple[AgentAssessment, ...],
    missing_domains: tuple[AgentDomain, ...],
    evidence_map: tuple,
    shared_limitations: tuple,
    unsupported_inferences: tuple,
) -> tuple[CoordinationFinding, ...]:
    findings: list[CoordinationFinding] = []
    if missing_domains:
        findings.append(
            CoordinationFinding(
                finding_code=CoordinationFindingCode.INCOMPLETE_DOMAIN_SET,
                severity=WarningSeverity.INFO,
                domains=missing_domains,
            )
        )
    if evidence_map and not any(record.cross_domain for record in evidence_map):
        findings.append(
            CoordinationFinding(
                finding_code=CoordinationFindingCode.NO_CROSS_DOMAIN_EVIDENCE,
                severity=WarningSeverity.LOW,
                source_ids=tuple(record.evidence_id for record in evidence_map),
            )
        )
    single_domain_sources = tuple(
        record.evidence_id for record in evidence_map if not record.cross_domain
    )
    if single_domain_sources:
        findings.append(
            CoordinationFinding(
                finding_code=CoordinationFindingCode.SINGLE_DOMAIN_ONLY_EVIDENCE,
                severity=WarningSeverity.INFO,
                source_ids=single_domain_sources,
            )
        )
    if all(
        not assessment.relevant_evidence_ids and not assessment.relevant_claim_ids
        for assessment in assessments
    ):
        findings.append(
            CoordinationFinding(
                finding_code=CoordinationFindingCode.ALL_AGENTS_EMPTY,
                severity=WarningSeverity.MEDIUM,
                domains=tuple(assessment.agent_domain for assessment in assessments),
            )
        )
    if any(record.global_limitation for record in shared_limitations):
        findings.append(
            CoordinationFinding(
                finding_code=CoordinationFindingCode.BROAD_SHARED_LIMITATION,
                severity=WarningSeverity.MEDIUM,
                domains=tuple(assessment.agent_domain for assessment in assessments),
            )
        )
    if any(
        record.inference_code is UnsupportedInferenceCode.CAUSALITY
        and record.all_participating_agents
        for record in unsupported_inferences
    ):
        findings.append(
            CoordinationFinding(
                finding_code=CoordinationFindingCode.BROAD_UNSUPPORTED_CAUSALITY_WARNING,
                severity=WarningSeverity.HIGH,
                domains=tuple(assessment.agent_domain for assessment in assessments),
            )
        )
    return tuple(sorted(findings, key=lambda item: item.finding_code.value))


def _coordinated_assessment_id(
    *,
    source_evidence_artifact_id: str,
    source_assessment_ids: tuple[str, ...],
    participating_domains: tuple[AgentDomain, ...],
) -> str:
    return deterministic_id(
        "coordinated_assessment_",
        {
            "source_evidence_artifact_id": source_evidence_artifact_id,
            "source_assessment_ids": tuple(sorted(source_assessment_ids)),
            "participating_domains": tuple(
                sorted(participating_domains, key=lambda domain: DOMAIN_ORDER.index(domain))
            ),
            "coordination_ruleset_version": COORDINATION_RULESET_VERSION,
            "schema_version": COORDINATION_SCHEMA_VERSION,
        },
    )
