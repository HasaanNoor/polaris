import json
from pathlib import Path

from polaris.agents.models import AgentAssessment, AgentDomain


def test_example_assessments_are_valid_and_illustrative():
    expected = {
        "governance_assessment.json": AgentDomain.GOVERNANCE,
        "economics_assessment.json": AgentDomain.ECONOMICS,
        "education_assessment.json": AgentDomain.EDUCATION,
        "public_health_assessment.json": AgentDomain.PUBLIC_HEALTH,
    }
    for filename, domain in expected.items():
        payload = json.loads((Path("examples/agents") / filename).read_text(encoding="utf-8"))
        assert payload["illustrative"] is True
        assessment = AgentAssessment.model_validate(payload["assessment"])
        assert assessment.agent_domain is domain
        assert "conclusion" not in payload["assessment"]
