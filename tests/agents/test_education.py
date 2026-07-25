from polaris.agents.models import AgentDomain, DomainConcernCode, UnsupportedInferenceCode
from polaris.agents.service import run_domain_agent
from polaris.evidence.models import LimitationCode


def test_education_selects_literacy_cross_domain_claim(cross_domain_artifact):
    assessment = run_domain_agent(
        domain=AgentDomain.EDUCATION,
        evidence_artifact=cross_domain_artifact,
    )

    assert "evidence_literacy" in assessment.relevant_evidence_ids
    assert "claim_literacy_fertility" in assessment.relevant_claim_ids
    assert LimitationCode.OBSERVATIONAL_ASSOCIATION in assessment.inherited_limitations
    concern_codes = {concern.concern_code for concern in assessment.domain_concerns}
    assert DomainConcernCode.CROSS_DOMAIN_RELATIONSHIP in concern_codes
    assert DomainConcernCode.UNSUPPORTED_POLICY_INFERENCE in concern_codes
    assert UnsupportedInferenceCode.POLICY_EFFECTIVENESS in assessment.unsupported_inferences
    assert "policy effectiveness" not in assessment.model_dump_json().lower()
