from polaris.agents.models import AgentDomain
from polaris.coordination import coordinate_assessments

from .helpers import assessment_for


def test_evidence_selected_by_one_domain(all_assessments):
    education = assessment_for(all_assessments, AgentDomain.EDUCATION)
    coordinated = coordinate_assessments(assessments=(education,))

    assert coordinated.evidence_domain_map
    assert all(not record.cross_domain for record in coordinated.evidence_domain_map)


def test_evidence_selected_by_multiple_domains(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    assert any(record.cross_domain for record in coordinated.evidence_domain_map)
    assert any(record.selection_count >= 2 for record in coordinated.evidence_domain_map)


def test_relevance_reason_preservation(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)
    mapped = next(record for record in coordinated.claim_domain_map if record.cross_domain)

    assert mapped.relevance_by_domain
    assert all(reference.relevance_reason_codes for reference in mapped.relevance_by_domain)


def test_claim_overlap_and_ordering(all_assessments):
    coordinated = coordinate_assessments(assessments=tuple(reversed(all_assessments)))
    claim_ids = tuple(record.claim_id for record in coordinated.claim_domain_map)

    assert claim_ids == tuple(sorted(claim_ids))
    assert any(record.cross_domain for record in coordinated.claim_domain_map)
    assert any(
        AgentDomain.ECONOMICS in record.selecting_domains for record in coordinated.claim_domain_map
    )
