from polaris.agents.models import AgentDomain, DomainConcernCode, UnsupportedInferenceCode
from polaris.agents.service import run_domain_agent
from polaris.evidence.models import LimitationCode

from .helpers import make_cross_domain_artifact


def test_governance_evidence_selected_without_invented_explanation():
    assessment = run_domain_agent(
        domain=AgentDomain.GOVERNANCE,
        evidence_artifact=make_cross_domain_artifact(include_governance=True),
    )

    assert "evidence_governance" in assessment.relevant_evidence_ids
    assert "evidence_literacy" not in assessment.relevant_evidence_ids
    assert LimitationCode.LIMITED_MODEL_SCOPE in assessment.inherited_limitations
    assert UnsupportedInferenceCode.CAUSALITY in assessment.unsupported_inferences
    assert DomainConcernCode.DIRECT_DOMAIN_VARIABLE in {
        concern.concern_code for concern in assessment.domain_concerns
    }
    assert "government effectiveness explains" not in assessment.model_dump_json().lower()


def test_governance_context_not_measured_for_cross_domain_claim_only(cross_domain_artifact):
    assessment = run_domain_agent(
        domain=AgentDomain.GOVERNANCE,
        evidence_artifact=cross_domain_artifact,
    )

    assert assessment.relevant_evidence_ids == ()
    assert DomainConcernCode.DOMAIN_CONTEXT_NOT_MEASURED in {
        concern.concern_code for concern in assessment.domain_concerns
    }
