"""Public-health domain agent."""

from polaris.agents.base import BaseDomainAgent
from polaris.agents.models import AgentDomain, UnsupportedInferenceCode


class PublicHealthAgent(BaseDomainAgent):
    domain = AgentDomain.PUBLIC_HEALTH

    def additional_unsupported_inferences(self) -> tuple[UnsupportedInferenceCode, ...]:
        return (UnsupportedInferenceCode.MEDICAL_CONCLUSION,)
