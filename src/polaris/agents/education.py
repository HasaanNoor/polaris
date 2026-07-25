"""Education domain agent."""

from polaris.agents.base import BaseDomainAgent
from polaris.agents.models import AgentDomain


class EducationAgent(BaseDomainAgent):
    domain = AgentDomain.EDUCATION
