import pytest

from polaris.agents.service import run_all_domain_agents
from polaris.coordination import coordinate_assessments
from tests.agents.helpers import make_cross_domain_artifact


@pytest.fixture
def synthesis_evidence_artifact():
    return make_cross_domain_artifact()


@pytest.fixture
def synthesis_assessments(synthesis_evidence_artifact):
    return run_all_domain_agents(evidence_artifact=synthesis_evidence_artifact)


@pytest.fixture
def coordinated(synthesis_assessments):
    return coordinate_assessments(assessments=synthesis_assessments)
