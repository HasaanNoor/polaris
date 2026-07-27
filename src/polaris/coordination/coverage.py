"""Domain coverage aggregation for Phase 7 coordination."""

from polaris.agents.models import AgentAssessment, CoverageStatus
from polaris.coordination.models import (
    DOMAIN_ORDER,
    CoordinationCoverageStatus,
    DomainCoverageRecord,
)


def aggregate_domain_coverage(
    assessments: tuple[AgentAssessment, ...],
) -> tuple[DomainCoverageRecord, ...]:
    by_domain = {assessment.agent_domain: assessment for assessment in assessments}
    records: list[DomainCoverageRecord] = []
    for domain in DOMAIN_ORDER:
        assessment = by_domain.get(domain)
        if assessment is None:
            records.append(
                DomainCoverageRecord(
                    domain=domain,
                    assessment_supplied=False,
                    coverage_status=CoordinationCoverageStatus.ASSESSMENT_MISSING,
                )
            )
            continue
        coverage_status = (
            CoordinationCoverageStatus.RELEVANT_EVIDENCE
            if assessment.coverage_summary.coverage_status is CoverageStatus.RELEVANT_EVIDENCE
            else CoordinationCoverageStatus.NO_RELEVANT_EVIDENCE
        )
        records.append(
            DomainCoverageRecord(
                domain=domain,
                assessment_supplied=True,
                assessment_id=assessment.assessment_id,
                relevant_evidence_count=assessment.coverage_summary.relevant_evidence_count,
                relevant_claim_count=assessment.coverage_summary.relevant_claim_count,
                direct_domain_variable_count=(
                    assessment.coverage_summary.direct_domain_variable_count
                ),
                cross_domain_claim_count=assessment.coverage_summary.cross_domain_claim_count,
                inherited_limitation_count=assessment.coverage_summary.limitations_count,
                domain_concern_count=len(assessment.domain_concerns),
                coverage_status=coverage_status,
            )
        )
    return tuple(records)
