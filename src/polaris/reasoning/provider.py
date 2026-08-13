"""Provider boundary for optional Phase 18 LLM reasoning."""

from typing import Protocol

from polaris.reasoning.models import ReasoningRequest, StructuredReasoningResponse

GroundingPayload = dict[str, object]


class ReasoningProvider(Protocol):
    provider_name: str

    def reason(
        self,
        *,
        request: ReasoningRequest,
        system_prompt: str,
        grounding_payload: GroundingPayload,
    ) -> StructuredReasoningResponse | dict:
        """Return structured reasoning over supplied artifact references only."""
