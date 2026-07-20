import pytest
from pydantic import ValidationError

from polaris.schemas.agents import AgentMessage, InsufficientEvidencePayload
from polaris.schemas.common import AgentMessageType


def test_valid_agent_message_creation(example_data):
    message = AgentMessage.model_validate(example_data["agent_message"])

    assert message.message_type == AgentMessageType.INVESTIGATION_REQUEST
    assert message.payload.payload_type == "investigation_request"


def test_agent_message_json_round_trip(example_data):
    message = AgentMessage.model_validate(example_data["agent_message"])

    assert AgentMessage.model_validate_json(message.model_dump_json()) == message


def test_agent_message_rejects_unknown_fields(example_data, copy_data):
    data = copy_data(example_data["agent_message"])
    data["payload"]["raw_payload"] = {"anything": "goes"}

    with pytest.raises(ValidationError):
        AgentMessage.model_validate(data)


def test_agent_message_requires_recipient(example_data, copy_data):
    data = copy_data(example_data["agent_message"])
    data["recipient_agent"] = None
    data["recipient_agents"] = []

    with pytest.raises(ValidationError):
        AgentMessage.model_validate(data)


def test_agent_message_discriminated_payload_parsing(example_data, copy_data):
    data = copy_data(example_data["agent_message"])
    data["message_type"] = "insufficient_evidence"
    data["payload"] = {
        "payload_type": "insufficient_evidence",
        "missing_evidence": ["approved dataset with comparable coverage"],
        "stop_condition": "no approved evidence source",
    }

    message = AgentMessage.model_validate(data)

    assert isinstance(message.payload, InsufficientEvidencePayload)
