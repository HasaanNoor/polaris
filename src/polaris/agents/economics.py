"""Economics domain agent."""

from polaris.agents.base import BaseDomainAgent
from polaris.agents.models import AgentDomain


class EconomicsAgent(BaseDomainAgent):
    domain = AgentDomain.ECONOMICS
