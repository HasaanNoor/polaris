"""Governance domain agent."""

from polaris.agents.base import BaseDomainAgent
from polaris.agents.models import AgentDomain


class GovernanceAgent(BaseDomainAgent):
    domain = AgentDomain.GOVERNANCE
