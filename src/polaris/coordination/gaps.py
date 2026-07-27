"""Deterministic evidence-gap and domain-gap identification."""

from polaris.agents.models import AgentDomain, RelevanceReasonCode
from polaris.coordination.models import (
    COORDINATION_RULESET_VERSION,
    COORDINATION_SCHEMA_VERSION,
    DOMAIN_ORDER,
    CoordinationCoverageStatus,
    DomainCoverageRecord,
    DomainGap,
    DomainGapType,
    EvidenceGap,
    EvidenceGapType,
)
from polaris.evidence.provenance import deterministic_id


def identify_domain_gaps(coverage: tuple[DomainCoverageRecord, ...]) -> tuple[DomainGap, ...]:
    gaps: list[DomainGap] = []
    for record in coverage:
        if not record.assessment_supplied:
            gaps.append(
                _domain_gap(
                    DomainGapType.DOMAIN_NOT_REPRESENTED,
                    domain=record.domain,
                    assessment_supplied=False,
                    coverage_status=record.coverage_status,
                )
            )
        elif record.coverage_status is CoordinationCoverageStatus.NO_RELEVANT_EVIDENCE:
            gaps.append(
                _domain_gap(
                    DomainGapType.DOMAIN_HAS_NO_RELEVANT_EVIDENCE,
                    domain=record.domain,
                    assessment_supplied=True,
                    coverage_status=record.coverage_status,
                )
            )
    return tuple(gaps)


def identify_evidence_gaps(*, evidence_map: tuple, claim_map: tuple) -> tuple[EvidenceGap, ...]:
    gaps: list[EvidenceGap] = []
    for record in evidence_map:
        if not record.cross_domain:
            gaps.append(
                _evidence_gap(
                    EvidenceGapType.EVIDENCE_REFERENCED_WITHOUT_CROSS_DOMAIN_CONTEXT,
                    source_ids=(record.evidence_id,),
                    domains=record.selecting_domains,
                )
            )
    for record in claim_map:
        if not record.cross_domain:
            gaps.append(
                _evidence_gap(
                    EvidenceGapType.CLAIM_SUPPORTED_BY_SINGLE_DOMAIN_ONLY,
                    source_ids=(record.claim_id,),
                    domains=record.selecting_domains,
                )
            )
        if record.cross_domain and _has_limited_domain_reason_coverage(record):
            gaps.append(
                _evidence_gap(
                    EvidenceGapType.CROSS_DOMAIN_CLAIM_WITH_LIMITED_DOMAIN_COVERAGE,
                    source_ids=(record.claim_id,),
                    domains=record.selecting_domains,
                )
            )
        if any(not reference.matched_variable_ids for reference in record.relevance_by_domain):
            gaps.append(
                _evidence_gap(
                    EvidenceGapType.LIMITED_VARIABLE_COVERAGE,
                    source_ids=(record.claim_id,),
                    domains=record.selecting_domains,
                )
            )
    return tuple(sorted(gaps, key=lambda item: (item.gap_type.value, item.gap_id)))


def _has_limited_domain_reason_coverage(record) -> bool:
    if set(record.selecting_domains) != set(DOMAIN_ORDER):
        return True
    return any(
        RelevanceReasonCode.DOMAIN_CONTROL_PRESENT in reference.relevance_reason_codes
        and RelevanceReasonCode.DIRECT_DOMAIN_VARIABLE not in reference.relevance_reason_codes
        for reference in record.relevance_by_domain
    )


def _domain_gap(
    gap_type: DomainGapType,
    *,
    domain: AgentDomain,
    assessment_supplied: bool,
    coverage_status: CoordinationCoverageStatus,
) -> DomainGap:
    payload = {
        "gap_type": gap_type,
        "domain": domain,
        "assessment_supplied": assessment_supplied,
        "coverage_status": coverage_status,
        "ruleset_version": COORDINATION_RULESET_VERSION,
        "schema_version": COORDINATION_SCHEMA_VERSION,
    }
    return DomainGap(
        gap_id=deterministic_id("coordination_domain_gap_", payload),
        gap_type=gap_type,
        domain=domain,
        assessment_supplied=assessment_supplied,
        coverage_status=coverage_status,
    )


def _evidence_gap(
    gap_type: EvidenceGapType,
    *,
    source_ids: tuple[str, ...],
    domains: tuple[AgentDomain, ...],
) -> EvidenceGap:
    ordered_domains = tuple(sorted(domains, key=lambda domain: DOMAIN_ORDER.index(domain)))
    payload = {
        "gap_type": gap_type,
        "source_ids": tuple(sorted(source_ids)),
        "domains": ordered_domains,
        "ruleset_version": COORDINATION_RULESET_VERSION,
        "schema_version": COORDINATION_SCHEMA_VERSION,
    }
    return EvidenceGap(
        gap_id=deterministic_id("coordination_evidence_gap_", payload),
        gap_type=gap_type,
        source_ids=source_ids,
        domains=ordered_domains,
    )
