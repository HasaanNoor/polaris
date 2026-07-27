import pytest
from pydantic import ValidationError

from polaris.agents.models import AgentDomain
from polaris.coordination import CoordinationRequest, coordinate_assessments


def test_valid_coordination_request(all_assessments):
    request = CoordinationRequest(assessments=all_assessments)

    assert request.assessments == all_assessments


def test_valid_coordinated_assessment_json_serializes(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)
    payload = coordinated.model_dump(mode="json")

    assert payload["coordinated_assessment_id"].startswith("coordinated_assessment_")
    assert payload["schema_version"] == "1.0.0"
    assert payload["participating_domains"] == [
        AgentDomain.GOVERNANCE.value,
        AgentDomain.ECONOMICS.value,
        AgentDomain.EDUCATION.value,
        AgentDomain.PUBLIC_HEALTH.value,
    ]
    assert "narrative" not in payload


def test_models_are_frozen(all_assessments):
    coordinated = coordinate_assessments(assessments=all_assessments)

    with pytest.raises(ValidationError):
        coordinated.dataset_id = "changed"


def test_unknown_fields_are_rejected(all_assessments):
    with pytest.raises(ValidationError):
        CoordinationRequest(assessments=all_assessments, extra_field=True)


def test_coordinated_id_is_deterministic(all_assessments):
    first = coordinate_assessments(assessments=all_assessments)
    second = coordinate_assessments(assessments=tuple(reversed(all_assessments)))

    assert first.coordinated_assessment_id == second.coordinated_assessment_id
