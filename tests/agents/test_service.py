import pytest

from polaris.agents.errors import UnsupportedAgentDomainError
from polaris.agents.models import AgentDomain
from polaris.agents.service import run_all_domain_agents, run_domain_agent


def test_run_all_domain_agents_returns_deterministic_order(cross_domain_artifact):
    assessments = run_all_domain_agents(evidence_artifact=cross_domain_artifact)

    assert tuple(assessment.agent_domain for assessment in assessments) == tuple(AgentDomain)


def test_unsupported_domain_error(cross_domain_artifact):
    with pytest.raises(UnsupportedAgentDomainError):
        run_domain_agent(domain="unknown", evidence_artifact=cross_domain_artifact)
