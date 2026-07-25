import pytest
from pydantic import ValidationError

from polaris.agents.models import (
    AgentAssessment,
    AgentDomain,
    CoverageStatus,
    DomainConcernCode,
)
from polaris.agents.service import run_domain_agent

from .helpers import make_cross_domain_artifact


def test_agent_domain_values_are_explicit():
    assert [domain.value for domain in AgentDomain] == [
        "governance",
        "economics",
        "education",
        "public_health",
    ]
    with pytest.raises(ValueError):
        AgentDomain("arbitrary")


def test_valid_assessment_is_immutable_and_rejects_unknown_fields(cross_domain_artifact):
    assessment = run_domain_agent(
        domain=AgentDomain.EDUCATION,
        evidence_artifact=cross_domain_artifact,
    )

    assert isinstance(assessment, AgentAssessment)
    assert assessment.coverage_summary.coverage_status is CoverageStatus.RELEVANT_EVIDENCE
    with pytest.raises(ValidationError):
        assessment.agent_domain = AgentDomain.GOVERNANCE
    with pytest.raises(ValidationError):
        AgentAssessment.model_validate({**assessment.model_dump(), "extra": True})


def test_assessment_ids_are_deterministic_and_ignore_timestamp():
    artifact = make_cross_domain_artifact()
    first = run_domain_agent(domain=AgentDomain.EDUCATION, evidence_artifact=artifact)
    second = run_domain_agent(domain=AgentDomain.EDUCATION, evidence_artifact=artifact)

    assert first.assessment_id == second.assessment_id
    assert first.model_dump(mode="json")["agent_domain"] == "education"
    assert "conclusion" not in first.model_dump()
    assert DomainConcernCode.UNSUPPORTED_CAUSAL_INFERENCE in {
        concern.concern_code for concern in first.domain_concerns
    }
