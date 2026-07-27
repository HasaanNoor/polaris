from polaris.agents.models import AgentDomain
from polaris.coordination import CoordinationCoverageStatus, coordinate_assessments

from .helpers import assessment_for, without_domain


def test_participating_and_missing_domains(all_assessments):
    coordinated = coordinate_assessments(
        assessments=without_domain(all_assessments, AgentDomain.GOVERNANCE)
    )

    assert coordinated.participating_domains == (
        AgentDomain.ECONOMICS,
        AgentDomain.EDUCATION,
        AgentDomain.PUBLIC_HEALTH,
    )
    assert coordinated.missing_domains == (AgentDomain.GOVERNANCE,)


def test_empty_domain_assessment_recorded(all_assessments):
    governance = assessment_for(all_assessments, AgentDomain.GOVERNANCE)
    coordinated = coordinate_assessments(assessments=all_assessments)
    coverage = next(
        record for record in coordinated.domain_coverage if record.domain is governance.agent_domain
    )

    assert coverage.assessment_supplied
    assert coverage.coverage_status is CoordinationCoverageStatus.NO_RELEVANT_EVIDENCE


def test_missing_domain_coverage_record(all_assessments):
    coordinated = coordinate_assessments(
        assessments=without_domain(all_assessments, AgentDomain.GOVERNANCE)
    )
    governance = coordinated.domain_coverage[0]

    assert governance.domain is AgentDomain.GOVERNANCE
    assert not governance.assessment_supplied
    assert governance.coverage_status is CoordinationCoverageStatus.ASSESSMENT_MISSING


def test_coverage_order_is_deterministic(all_assessments):
    coordinated = coordinate_assessments(assessments=tuple(reversed(all_assessments)))

    assert tuple(record.domain for record in coordinated.domain_coverage) == (
        AgentDomain.GOVERNANCE,
        AgentDomain.ECONOMICS,
        AgentDomain.EDUCATION,
        AgentDomain.PUBLIC_HEALTH,
    )
