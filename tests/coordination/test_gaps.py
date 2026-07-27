from polaris.agents.models import AgentDomain
from polaris.coordination import DomainGapType, EvidenceGapType, coordinate_assessments

from .helpers import assessment_for, without_domain


def test_missing_domain_gap(all_assessments):
    coordinated = coordinate_assessments(
        assessments=without_domain(all_assessments, AgentDomain.GOVERNANCE)
    )

    assert any(
        gap.gap_type is DomainGapType.DOMAIN_NOT_REPRESENTED for gap in coordinated.domain_gaps
    )


def test_domain_with_no_relevant_evidence_gap(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert any(
        gap.domain is AgentDomain.GOVERNANCE
        and gap.gap_type is DomainGapType.DOMAIN_HAS_NO_RELEVANT_EVIDENCE
        for gap in coordinated.domain_gaps
    )


def test_single_domain_claim_and_evidence_gaps(all_assessments):
    coordinated = coordinate_assessments(
        assessments=(assessment_for(all_assessments, AgentDomain.EDUCATION),)
    )
    gap_types = {gap.gap_type for gap in coordinated.evidence_gaps}

    assert EvidenceGapType.CLAIM_SUPPORTED_BY_SINGLE_DOMAIN_ONLY in gap_types
    assert EvidenceGapType.EVIDENCE_REFERENCED_WITHOUT_CROSS_DOMAIN_CONTEXT in gap_types


def test_cross_domain_claim_with_limited_coverage_gap(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert any(
        gap.gap_type is EvidenceGapType.CROSS_DOMAIN_CLAIM_WITH_LIMITED_DOMAIN_COVERAGE
        for gap in coordinated.evidence_gaps
    )


def test_all_empty_assessments_are_valid(unrelated_assessment):
    coordinated = coordinate_assessments(assessments=(unrelated_assessment,))

    assert not coordinated.evidence_domain_map
    assert not coordinated.claim_domain_map
    assert not any(
        "government effectiveness" in gap.model_dump_json() for gap in coordinated.evidence_gaps
    )
