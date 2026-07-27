import pytest

from polaris.agents.service import run_all_domain_agents, run_domain_agent
from tests.agents.helpers import make_cross_domain_artifact, make_unrelated_artifact


@pytest.fixture
def cross_domain_artifact():
    return make_cross_domain_artifact()


@pytest.fixture
def unrelated_artifact():
    return make_unrelated_artifact()


@pytest.fixture
def all_assessments(cross_domain_artifact):
    return run_all_domain_agents(evidence_artifact=cross_domain_artifact)


@pytest.fixture
def unrelated_assessment(unrelated_artifact):
    from polaris.agents.models import AgentDomain

    return run_domain_agent(domain=AgentDomain.EDUCATION, evidence_artifact=unrelated_artifact)
