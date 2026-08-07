from pathlib import Path

import pytest
from pydantic import ValidationError

from polaris.agents.models import AgentDomain
from polaris.projects import ResearchProjectRequest
from tests.projects.helpers import single_manifest_project


def test_valid_request_is_frozen_and_sorts_agents(tmp_path: Path) -> None:
    request = single_manifest_project(tmp_path).model_copy(
        update={"selected_agents": (AgentDomain.PUBLIC_HEALTH, AgentDomain.ECONOMICS)}
    )

    validated = ResearchProjectRequest.model_validate(request.model_dump(mode="python"))

    assert validated.selected_agents == (AgentDomain.ECONOMICS, AgentDomain.PUBLIC_HEALTH)
    with pytest.raises(ValidationError):
        validated.project_name = "changed"  # type: ignore[misc]


def test_unknown_field_rejected(tmp_path: Path) -> None:
    payload = single_manifest_project(tmp_path).model_dump(mode="python")
    payload["unexpected"] = True

    with pytest.raises(ValidationError):
        ResearchProjectRequest.model_validate(payload)


def test_request_serialization_is_deterministic(tmp_path: Path) -> None:
    request = single_manifest_project(tmp_path)

    assert request.model_dump_json() == request.model_dump_json()
