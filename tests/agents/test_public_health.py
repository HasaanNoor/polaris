from polaris.agents.models import AgentDomain, DomainConcernCode, UnsupportedInferenceCode
from polaris.agents.service import run_domain_agent
from polaris.evidence.models import LimitationCode


def test_public_health_selects_fertility_relationship_without_medical_inference(
    cross_domain_artifact,
):
    assessment = run_domain_agent(
        domain=AgentDomain.PUBLIC_HEALTH,
        evidence_artifact=cross_domain_artifact,
    )

    assert "claim_literacy_fertility" in assessment.relevant_claim_ids
    assert "evidence_sample" in assessment.relevant_evidence_ids
    assert LimitationCode.UNSUPPORTED_GENERALIZATION in assessment.inherited_limitations
    assert DomainConcernCode.CROSS_DOMAIN_RELATIONSHIP in {
        concern.concern_code for concern in assessment.domain_concerns
    }
    assert UnsupportedInferenceCode.MEDICAL_CONCLUSION in assessment.unsupported_inferences
    assert "medical advice" not in assessment.model_dump_json().lower()
