from polaris.agents.models import AgentDomain, RelevanceReasonCode, RelevanceStatus
from polaris.agents.relevance import classify_variable
from polaris.agents.service import run_all_domain_agents, run_domain_agent

from .helpers import make_cross_domain_artifact, make_unrelated_artifact


def test_direct_variable_mappings():
    assert classify_variable("government_effectiveness")
    assert classify_variable("gdp_per_capita")
    assert classify_variable("female_literacy")
    assert classify_variable("fertility_rate")


def test_cross_domain_relevance_and_unrelated_variable():
    artifact = make_cross_domain_artifact()
    education = run_domain_agent(domain=AgentDomain.EDUCATION, evidence_artifact=artifact)
    health = run_domain_agent(domain=AgentDomain.PUBLIC_HEALTH, evidence_artifact=artifact)
    economics = run_domain_agent(domain=AgentDomain.ECONOMICS, evidence_artifact=artifact)
    governance = run_domain_agent(domain=AgentDomain.GOVERNANCE, evidence_artifact=artifact)

    assert "claim_literacy_fertility" in education.relevant_claim_ids
    assert "claim_literacy_fertility" in health.relevant_claim_ids
    assert "claim_gdp_fertility" in economics.relevant_claim_ids
    assert governance.relevant_claim_ids == ()


def test_conservative_keyword_fallback_has_no_fuzzy_matching():
    assert classify_variable("adult_literacy_total")
    assert classify_variable("literac") == ()


def test_relevance_ordering_is_deterministic():
    artifact = make_cross_domain_artifact()
    first = run_all_domain_agents(evidence_artifact=artifact)
    second = run_all_domain_agents(evidence_artifact=artifact)

    assert [assessment.agent_domain for assessment in first] == [
        AgentDomain.GOVERNANCE,
        AgentDomain.ECONOMICS,
        AgentDomain.EDUCATION,
        AgentDomain.PUBLIC_HEALTH,
    ]
    assert [assessment.assessment_id for assessment in first] == [
        assessment.assessment_id for assessment in second
    ]


def test_empty_relevance_is_valid_and_explainable():
    assessment = run_domain_agent(
        domain=AgentDomain.GOVERNANCE,
        evidence_artifact=make_unrelated_artifact(),
    )

    assert assessment.relevant_evidence_ids == ()
    assert assessment.relevant_claim_ids == ()
    assert all(
        record.relevance_status is RelevanceStatus.NOT_RELEVANT
        for record in assessment.domain_relevance_records
    )
    assert all(
        RelevanceReasonCode.NO_DOMAIN_MATCH in record.relevance_reason_codes
        for record in assessment.domain_relevance_records
    )
