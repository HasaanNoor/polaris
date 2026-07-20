"""Agent message schema."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from polaris.schemas.common import (
    AgentId,
    AgentMessageStatus,
    AgentMessageType,
    ArtifactReference,
    AwareDatetime,
    EvidenceReference,
    InvestigationId,
    MessageId,
    NonEmptyStr,
    PolarisBaseModel,
    SchemaVersion,
    ValidationWarning,
)


class InvestigationRequestPayload(PolarisBaseModel):
    payload_type: Literal["investigation_request"]
    question_id: NonEmptyStr
    requested_agents: list[AgentId] = Field(min_length=1)
    priority: NonEmptyStr | None = None


class AgentContributionPayload(PolarisBaseModel):
    payload_type: Literal["agent_contribution"]
    agent_role: NonEmptyStr
    contribution_summary: NonEmptyStr
    output_references: list[NonEmptyStr] = Field(default_factory=list)
    validation_status: NonEmptyStr


class ValidationFailurePayload(PolarisBaseModel):
    payload_type: Literal["validation_failure"]
    failed_fields: list[NonEmptyStr] = Field(min_length=1)
    reason: NonEmptyStr


class InsufficientEvidencePayload(PolarisBaseModel):
    payload_type: Literal["insufficient_evidence"]
    missing_evidence: list[NonEmptyStr] = Field(min_length=1)
    stop_condition: NonEmptyStr


class CompletionNotificationPayload(PolarisBaseModel):
    payload_type: Literal["completion_notification"]
    artifact_id: NonEmptyStr
    artifact_version: NonEmptyStr
    final_status: NonEmptyStr


AgentPayload = Annotated[
    InvestigationRequestPayload
    | AgentContributionPayload
    | ValidationFailurePayload
    | InsufficientEvidencePayload
    | CompletionNotificationPayload,
    Field(discriminator="payload_type"),
]


class AgentMessage(PolarisBaseModel):
    """Typed communication envelope for deterministic or future LLM-backed agents."""

    message_id: MessageId
    investigation_id: InvestigationId
    sender_agent: AgentId
    recipient_agent: AgentId | None = None
    recipient_agents: list[AgentId] = Field(default_factory=list)
    message_type: AgentMessageType
    timestamp: AwareDatetime
    correlation_id: MessageId | None = None
    parent_message_id: MessageId | None = None
    status: AgentMessageStatus
    payload: AgentPayload
    warnings: list[ValidationWarning] = Field(default_factory=list)
    errors: list[NonEmptyStr] = Field(default_factory=list)
    evidence_references: list[EvidenceReference] = Field(default_factory=list)
    artifact_references: list[ArtifactReference] = Field(default_factory=list)
    schema_version: SchemaVersion = "1.0.0"

    @model_validator(mode="after")
    def require_recipient(self) -> "AgentMessage":
        if self.recipient_agent is None and not self.recipient_agents:
            raise ValueError("at least one recipient agent is required")
        return self
