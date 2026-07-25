from polaris.agents.models import AgentDomain, DomainConcernCode, UnsupportedInferenceCode
from polaris.agents.service import run_domain_agent
from polaris.evidence.models import LimitationCode


def test_economics_selects_gdp_control_and_preserves_limitations(cross_domain_artifact):
    assessment = run_domain_agent(
        domain=AgentDomain.ECONOMICS,
        evidence_artifact=cross_domain_artifact,
    )

    assert "evidence_gdp" in assessment.relevant_evidence_ids
    assert "evidence_literacy" in assessment.relevant_evidence_ids
    assert "claim_literacy_fertility" in assessment.relevant_claim_ids
    assert LimitationCode.MISSING_DATA_EXCLUSION in assessment.inherited_limitations
    assert DomainConcernCode.DOMAIN_CONTROL_PRESENT in {
        concern.concern_code for concern in assessment.domain_concerns
    }
    assert UnsupportedInferenceCode.MECHANISM in assessment.unsupported_inferences
    assert "mechanism" not in assessment.model_dump()
