"""Public API for deterministic Phase 6 domain agents."""

from polaris.agents.base import DomainAgent
from polaris.agents.economics import EconomicsAgent
from polaris.agents.education import EducationAgent
from polaris.agents.errors import UnsupportedAgentDomainError
from polaris.agents.governance import GovernanceAgent
from polaris.agents.models import AgentAssessment, AgentDomain
from polaris.agents.public_health import PublicHealthAgent
from polaris.evidence.models import EvidenceArtifact

AGENT_EXECUTION_ORDER: tuple[AgentDomain, ...] = (
    AgentDomain.GOVERNANCE,
    AgentDomain.ECONOMICS,
    AgentDomain.EDUCATION,
    AgentDomain.PUBLIC_HEALTH,
)


def run_domain_agent(
    *,
    domain: AgentDomain,
    evidence_artifact: EvidenceArtifact,
) -> AgentAssessment:
    """Run one deterministic domain agent against a Phase 5 evidence artifact."""

    agent = _agent_for_domain(domain)
    return agent.assess(evidence_artifact)


def run_all_domain_agents(*, evidence_artifact: EvidenceArtifact) -> tuple[AgentAssessment, ...]:
    """Run all core domain agents in deterministic order without synthesis."""

    return tuple(
        run_domain_agent(domain=domain, evidence_artifact=evidence_artifact)
        for domain in AGENT_EXECUTION_ORDER
    )


def _agent_for_domain(domain: AgentDomain) -> DomainAgent:
    try:
        normalized = AgentDomain(domain)
    except ValueError as exc:
        raise UnsupportedAgentDomainError(f"unsupported agent domain: {domain}") from exc
    agents: dict[AgentDomain, DomainAgent] = {
        AgentDomain.GOVERNANCE: GovernanceAgent(),
        AgentDomain.ECONOMICS: EconomicsAgent(),
        AgentDomain.EDUCATION: EducationAgent(),
        AgentDomain.PUBLIC_HEALTH: PublicHealthAgent(),
    }
    return agents[normalized]
