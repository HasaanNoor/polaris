"""Minimal provider boundary for Phase 8 LLM-assisted synthesis."""

from typing import Protocol

from polaris.synthesis.models import GroundingPayload, StructuredSynthesisResponse, SynthesisRequest


class SynthesisProvider(Protocol):
    """Small protocol implemented by mocked or real LLM synthesis providers."""

    provider_name: str

    def synthesize(
        self,
        *,
        request: SynthesisRequest,
        system_prompt: str,
        grounding_payload: GroundingPayload,
    ) -> StructuredSynthesisResponse | dict:
        """Return a structured synthesis response for the supplied grounding payload."""
